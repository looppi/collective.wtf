from zope.interface import implements
from zope.component import adapts

from collective.wtf.interfaces import ISanityChecker
from Products.DCWorkflow.interfaces import IDCWorkflowDefinition
from Products.CMFCore import permissions as cmf_permissions

from plone.memoize.instance import memoize

from collective.wtf.exportimport import CSVWorkflowDefinitionConfigurator

class BaseChecker(object):
    implements(ISanityChecker)
    
    def __init__(self, context):
        self.context = context

    @memoize
    def info(self):
        wfdc = CSVWorkflowDefinitionConfigurator(self.context)
        return wfdc.getWorkflowInfo(self.context.getId())

class StateVariable(BaseChecker):
    adapts(IDCWorkflowDefinition)
    
    expected_state_variable = 'review_state'
    
    def __call__(self):
        messages = []
        state_variable = self.info()['state_variable']
        if state_variable != self.expected_state_variable:
            messages.append("The state variable should be '%s', but is defined as '%s'" % (self.expected_state_variable, state_variable))
        return messages
    
class CorePermissions(BaseChecker):
    adapts(IDCWorkflowDefinition)
    
    expected_permissions = set((cmf_permissions.View, cmf_permissions.AccessContentsInformation, cmf_permissions.ModifyPortalContent),)
    
    def __call__(self):
        messages = []
        for state in self.info()['state_info']:
            missing = self.expected_permissions - set([p['name'] for p in state['permissions']])
            for name in missing:
                messages.append("State '%s' does not assign roles to the core permission '%s'" % (state['id'], name))
        return messages
    
class AnonymousPreference(BaseChecker):
    adapts(IDCWorkflowDefinition)
    
    def __call__(self):
        messages = []
        for state in self.info()['state_info']:
            for permission in state['permissions']:
                roles = permission['roles']
                if 'Anonymous' in roles and len(roles) > 1:
                    messages.append("State '%s' grants permission '%s' to Anonymous. Other role assignments are superfluous." % (state['id'], permission['name']))
        return messages
    
class ViewVsAccess(BaseChecker):
    adapts(IDCWorkflowDefinition)
    
    def __call__(self):
        messages = []
        for state in self.info()['state_info']:
            permissions = dict([(p['name'], p) for p in state['permissions']])
            if cmf_permissions.View in permissions and cmf_permissions.AccessContentsInformation in permissions:
                if set(permissions[cmf_permissions.View]['roles']) != set(permissions[cmf_permissions.AccessContentsInformation]['roles']):
                    messages.append("State '%s' defines different roles for the 'View' and 'Access contents information' permissions." % state['id'])
                if permissions[cmf_permissions.View]['acquired'] != permissions[cmf_permissions.AccessContentsInformation]['acquired']:
                    messages.append("State '%s' defines different acquire flags for the 'View' and 'Access contents information' permissions." % state['id'])
        return messages

class LocalRoleCorrelation(BaseChecker):
    adapts(IDCWorkflowDefinition)
    
    permissions_for_owner_and_reader = set((cmf_permissions.View, cmf_permissions.AccessContentsInformation,))
    permissions_for_owner_and_editor = set((cmf_permissions.View, cmf_permissions.AccessContentsInformation, cmf_permissions.ModifyPortalContent))
    permissions_for_owner_and_contributor = set((cmf_permissions.View, cmf_permissions.AccessContentsInformation, cmf_permissions.AddPortalContent))    
    
    def __call__(self):
        messages = []
        self._role_correlation(messages, self.permissions_for_owner_and_reader, 'Owner', 'Reader')
        self._role_correlation(messages, self.permissions_for_owner_and_editor, 'Owner', 'Editor')
        self._role_correlation(messages, self.permissions_for_owner_and_contributor, 'Owner', 'Contributor')
        return messages
    
    def _role_correlation(self, messages, permission_set, role1, role2):
        for state in self.info()['state_info']:
            for permission in state['permissions']:
                if permission['name'] in permission_set:
                    roles = permission['roles']
                    if role1 in roles and role2 not in roles:
                        messages.append("State '%s' grants permission '%s' to '%s', but not to '%s'" % (state['id'], permission['name'], role1, role2,))
                    elif role1 not in roles and role2 in roles:
                        messages.append("State '%s' grants permission '%s' to '%s', but not to '%s'" % (state['id'], permission['name'], role1, role2,))
    
class WorkflowVariables(BaseChecker):
    adapts(IDCWorkflowDefinition)
    
    expected_variables = set(('action', 'actor', 'comments', 'review_history', 'time'))
    
    def __call__(self):
        messages = []
        variable_ids = set([v['id'] for v in self.info()['variable_info']])
        for variable in self.expected_variables:
            if variable not in variable_ids:
                messages.append("The workflow variable '%s' is not defined" % variable)
        return messages