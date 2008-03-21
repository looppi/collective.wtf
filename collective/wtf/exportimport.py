import os.path
import csv
from StringIO import StringIO

from zope.component import queryMultiAdapter

from Products.GenericSetup.interfaces import IBody
from Products.GenericSetup.interfaces import ISetupEnviron
from Products.GenericSetup.utils import BodyAdapterBase

from Products.DCWorkflow.interfaces import IDCWorkflowDefinition
from Products.DCWorkflow.exportimport import WorkflowDefinitionConfigurator
from Products.DCWorkflow.exportimport import _initDCWorkflow

from zope.component import adapts

from collective.wtf import config


class DCWorkflowDefinitionBodyAdapter(BodyAdapterBase):
    """Body im- and exporter for DCWorkflowDefinition in CSV format.
    """

    adapts(IDCWorkflowDefinition, ISetupEnviron)
    
    def _exportBody(self):
        """Return the most commonly used aspects of a workflow as a CSV
        file string.
        """
        
        wfdc = WorkflowDefinitionConfigurator(self.context)
        
        # CMF folks, we love you
        i = wfdc.getWorkflowInfo(self.context.getId())
        
        custom_roles = set()
        for s in i['state_info']:
            for p in s['permissions']:
                for r in p['roles']:
                    if r not in config.KNOWN_ROLES:
                        custom_roles.add(r)
        all_roles = config.KNOWN_ROLES + sorted(custom_roles)
        
        state_worklists = {}
        for w in i['worklist_info']:
            for v in w['var_match']:
                if v[0] == 'review_state':
                    state_worklists[v[1]] = w
        
        output = StringIO()
        writer = csv.writer(output)
        
        r = writer.writerow
        
        r(['[Workflow]'])
        r(['Id:',            i['id']                  ])
        r(['Title:',         i['title'].strip()       ])
        r(['Description:',   i['description'].strip() ])
        r(['Initial state:', i['initial_state']       ])
        r([]) # terminator row
        
        for s in i['state_info']:
            r(['[State]'])
            r(['Id:',           s['id']                     ])
            r(['Title:',        s['title'].strip()          ])
            r(['Description:',  s['description'].strip()    ])
            r(['Transitions',   ', '.join(s['transitions']) ])
            
            w = state_worklists.get(s['id'], None)
            if w is not None:
                r(['Worklist:',                  w['description']                  ])
                r(['Worklist label:',            w['actbox_name']                  ])
                r(['Worklist guard permission:', ', '.join(w['guard_permissions']) ])
                r(['Worklist guard role:',       ', '.join(w['guard_roles'])       ])
                r(['Worklist guard expression:', w['guard_expr']                   ])
            
            r(['Permissions', 'Acquire'] + all_roles)
            
            permission_map = dict([p['name'], p] for p in s['permissions'])
            ordered_permissions = [permission_map[p] for p in config.KNOWN_PERMISSIONS if p in permission_map] + \
                                  [p for p in s['permissions'] if p['name'] not in config.KNOWN_PERMISSIONS]

            for p in ordered_permissions:
                acquired = 'N'
                if p['acquired']:
                    acquired = 'Y'
                
                role_map = []
                for role in all_roles:
                    if role in p['roles']:
                        role_map.append('Y')
                    else:
                        role_map.append('N')
                    
                r([p['name'], acquired] + role_map)
            
            r([]) # terminator row
            
        for t in i['transition_info']:
            r(['[Transition]'])
            
            r(['Id:',               t['id']                             ])
            r(['Target state:',     t['new_state_id']                   ])
            r(['Title:',            t['actbox_name']                    ])
            r(['Description:',      t['description'].strip()            ])
            r(['Trigger:',          t['trigger_type'].capitalize()      ])
            r(['Script before:',    t['script_name']                    ])
            r(['Script after:',     t['after_script_name']              ])
            
            r(['Guard permission:', ', '.join(t['guard_permissions'])   ])
            r(['Guard role:',       ', '.join(t['guard_roles'])         ])
            r(['Guard expression:', t['guard_expr']                     ])

            r([]) # terminator row
            
        return output.getvalue()

    def _importBody(self, body):
        """Import the object from the file body.
        """
        
        i = config.INFO_TEMPLATE.copy()
        
        _initDCWorkflow(self.context, 
                        i['title'],          i['description'],     i['state_variable'], 
                        i['initial_state'],  i['state_info'],      i['transition_info'], 
                        i['variable_info'],  i['worklist_info'],   i['permissions'], 
                        i['script_info'],
                        self.environ)

    body = property(_exportBody, _importBody)

def importCSVWorkflow(context):
    """Import portlet managers and portlets
    """
    
    site = context.getSite()
    portal_workflow = getattr(site, 'portal_workflow', None)
    
    if portal_workflow is None:
        return None
    
    for wf in portal_workflow.objectValues():
        
        filename = os.path.join("workflow_csv", "/%s.csv" % wf.getId())
        xml_filename = os.path.join("workflows", wf.getId(), "definition.xml")
        
        if not os.path.exists(filename):
            continue
        
        if os.path.exists(xml_filename):
            logger = context.getLogger('workflow-csv')
            logger.warn('Skipping CSV workflow definition in %s since %s exists' % (filename, xml_filename))
            continue
        
        importer = queryMultiAdapter((wf, context), IBody, name=u'collective.wtf')
        
        body = context.readDataFile(filename)
        if body is not None:
            importer.filename = filename # for error reporting
            importer.body = body

def exportCSVWorkflow(context):
    """Export portlet managers and portlets
    """
    site = context.getSite()
    portal_workflow = getattr(site, 'portal_workflow', None)
    
    if portal_workflow is None:
        return None
    
    for wf in portal_workflow.objectValues():
        exporter = queryMultiAdapter((wf, context), IBody, name=u'collective.wtf')
        
        if not os.path.exists('workflow_csv'):
            os.mkdir('workflow_csv')
        
        filename = os.path.join("workflow_csv", "%s.csv" % wf.getId())
        body = exporter.body
        if body is not None:
            context.writeDataFile(filename, body, 'text/csv')