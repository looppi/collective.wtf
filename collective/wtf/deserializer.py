import copy
import csv
import re

from zope.interface import implements
from zope.component import getUtility

from collective.wtf.interfaces import ParsingError
from collective.wtf.interfaces import ICSVWorkflowDeserializer
from collective.wtf.interfaces import ICSVWorkflowConfig

any_whitespace = re.compile(r'\s+')
not_alnum = re.compile(r'[^a-z1-9-]')
section_pattern = re.compile(r'^\s*\[.+\]\s*$')

import logging
logger = logging.getLogger()

class DefaultDeserializer(object):
    implements(ICSVWorkflowDeserializer)

    def __init__(self):
        self.handlers = dict(workflow=self.parse_workflow,
                             state=self.parse_state,
                             transition=self.parse_transition)

    def __call__(self, input_stream, config_variant=u""):

        config = getUtility(ICSVWorkflowConfig, name=config_variant)
        reader = csv.reader(input_stream)
    
        info = copy.deepcopy(config.info_template)
        
        self.dispatch(config, info, reader)
        self.backfill(info)
        self.validate(info)
    
        return info

    # parsing methods

    def dispatch(self, config, info, reader):
        """Dispatch to an appropriate section handler
        """
        
        checklist = set(['workflow', 'state',])
        found = set()
        
        for line in reader:
            section = self.read_section(line)
            
            if section in checklist:
                found.add(section)
                
            handler = self.handlers.get(section, None)
            if handler:
                handler(config, info, reader)
                
        missing = checklist - found
        if len(missing) == 1:
            raise ParsingError("Expected to find a [%s] section." % list(missing)[0].capitalize())
        elif len(missing) > 1:
            raise ParsingError("Expected to find at least one of each of these sections: %s" % ', '.join(["[%s]" % m.capitalize() for m in missing]))
    
    def parse_workflow(self, config, info, reader):
        """Parse a [Workflow] section
        """
        wf_info = self.get_map(reader)
        
        required = ['id', 'initial-state']
        missing = [m for m in required if m not in wf_info]
        if missing:
            raise ParsingError("The [Workflow] section must have an 'Id:' and an 'Initial state:' defined")
        
        info['id']            = wf_info['id']
        info['initial_state'] = wf_info['initial-state']
        
        info['title']         = wf_info.get('title', '')
        info['description']   = wf_info.get('description', '')
        
    def parse_state(self, config, info, reader):
        """Parse a [State] section
        """
        
        s_info = self.get_map(reader, stop='permissions')
        
        required = ['id', 'title']
        missing = [m for m in required if m not in s_info]
        if missing:
            raise ParsingError("The [State] section must have an 'Id:' and a 'Title:' defined")
    
        if 'permissions' not in s_info:
            raise ParsingError("The [State] section must end with a 'Permissions' table")
            
        roles = s_info['permissions'][1:]
        if not roles or self.normalize(roles[0]) not in ('acquire', 'acquired',):
            raise ParsingError("The [State] section must end with a 'Permissions' table that contains role names along the top row, starting with 'Acquired'")
        roles = [r.strip() for r in roles[1:]] # ignore the "acquire" column
        
        state = copy.deepcopy(config.state_template)
        
        # Set basic properties
        state['id']          = s_info['id']
        state['title']       = s_info['title']
        state['transitions'] = self.get_list(s_info.get('transitions', ''))

        # Populate permission/role mappings
        for line in reader:
            if not line or not ''.join(line): #  EOF or blank line:
                break

            permission_info = copy.deepcopy(config.state_permission_template)
            permission_info['name'] = line[0].strip()
            
            if len(line) >= 2: # we have a value in the 'acquired' column
                permission_info['acquired'] = self.get_bool(line[1])
                
            if len(line) >= 3: # we have some permissions
                mapped_roles = line[2:]
                permission_roles = set()
                for idx in range(len(roles)):
                    if idx >= len(mapped_roles):
                        break
                        
                    if self.get_bool(mapped_roles[idx]):
                        permission_roles.add(roles[idx])
                permission_info['roles'] = sorted(permission_roles)
            
            state['permissions'].append(permission_info)
        
        info['state_info'].append(state)

        # Populate worklist if any
        if 'worklist' in s_info:
            
            worklist = copy.deepcopy(config.worklist_template)
            
            worklist['id']                = self.normalize(s_info['worklist'])
            worklist['actbox_name']       = s_info.get('worklist-label', '')
            worklist['description']       = s_info['worklist'] 
            worklist['actbox_url']        = '%(portal_url)s/search?review_state=' + state['id']
            worklist['guard_roles']       = self.get_list(s_info.get('worklist-guard-role', s_info.get('worklist-guard-roles', '')))
            worklist['guard_permisisons'] = self.get_list(s_info.get('worklist-guard-permission', s_info.get('worklist-guard-permissions', '')))
            worklist['guard_expr']        = s_info.get('worklist-guard-expression', '')
            worklist['var_match']         = [('review_state', state['id'])]
            
            info['worklist_info'].append(worklist)
        
        
    def parse_transition(self, config, info, reader):
        """Parse a [Transition] section
        """
        
        t_info = self.get_map(reader)
        
        required = ['id', 'target-state', 'title']
        missing = [m for m in required if m not in t_info]
        if missing:
            raise ParsingError("Each [Transition] section must have an 'Id:', a 'Title:' and a 'Target state:' defined")
        
        transition = copy.deepcopy(config.transition_template)
        
        transition['id']                = t_info['id']
        transition['new_state_id']      = t_info['target-state']
        transition['actbox_name']       = t_info['title']
        transition['title']             = t_info.get('description', '') # yes, this is right
        transition['description']       = t_info.get('details', '')
        transition['trigger_type']      = t_info.get('trigger', 'User').upper()
        transition['actbox_url']        = "%(content_url)s/content_status_modify?workflow_action=" + t_info['id']
        transition['guard_roles']       = self.get_list(t_info.get('guard-role', t_info.get('guard-roles', '')))
        transition['guard_permisisons'] = self.get_list(t_info.get('guard-permission', t_info.get('guard-permissions', '')))
        transition['guard_expr']        = t_info.get('guard-expression', '')
        
        info['transition_info'].append(transition)
        
    # integrity methods

    def backfill(self, info):
        """Fill in the bits of the info dict that can be inferred from other
        bits.
        """
        
        all_permissions = set()
        for s in info['state_info']:
            for p in s['permissions']:
                all_permissions.add(p['name'])

        info['permissions'] = sorted(all_permissions)
        
    def validate(self, info):
        """Perform overall validation on the workflow
        """
        
        state_ids = set([s['id'] for s in info['state_info']])
        if info['initial_state'] not in state_ids:
            raise ParsingError("The initial state id is set to %s, but this is not found in the workflow" % info['initial_state'])
            
        
        
    # helper methods
        
    def read_section(self, line):
        """Return a normalized section name
        """
        if not line or not ''.join(line): #  EOF or blank line:
            return None
            
        cell = line[0]
        if not section_pattern.match(cell):
            return None
            
        return self.normalize(cell)
        
        
    def get_map(self, reader, stop=None):
        """Read all values until a blank line or the 'stop' line are hit.
        If the 'stop' line is hit, it will be included under that key in
        full, as a list, so that the line is not lost.
        """
        values = {}
        
        for line in reader:
            
            if not line or not ''.join(line): #  EOF or blank line
                break

            if len(line) < 2:
                logger.warning("Expected key/value pair on line %s, skipping" % ','.join(line))
                continue
            
            key = self.normalize(line[0])
            value = line[1].strip()
            
            if value:
                values[key] = line[1].strip()
            
            if stop and key == stop:
                values[key] = line
                break
            
        return values
        
    def normalize(self, cell):
        """Make a cell value lowercase, remove non-alphanumeric characters, 
        strip leading and trailing whitespace, replace other whitespace with 
        dashes, and return.
        """
        
        cell = cell.lower().strip()
        cell = any_whitespace.sub('-', cell)
        cell = not_alnum.sub('', cell)
        return cell
        
    def get_list(self, value):
        """Turn a cell value containing comma-separated values into a list.
        """
        return [v.strip() for v in value.split(',')]
        
    def get_bool(self, value):
        """Return a boolean representation of a cell value
        """
        
        value = value.strip().lower()
        
        if not value: # empty string, None, False
            return False

        if value in ('x', '*',):
            return True
        
        if value.startswith('y'):
            return True
            
        return False