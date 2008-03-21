import difflib
import unittest
from StringIO import StringIO

import zope.component
import zope.component.testing

from collective.wtf.config import DefaultConfig
from collective.wtf.deserializer import DefaultDeserializer
from collective.wtf.serializer import DefaultSerializer

class ConfigLayer:
    
    @classmethod
    def setUp(cls):
        zope.component.provideUtility(DefaultConfig())

    @classmethod
    def tearDown(cls):
        zope.component.testing.tearDown()

class TestSerializer(unittest.TestCase):
    
    layer = ConfigLayer
    
    def test_serialize_complex(self):
        info = plone_workflow_info.copy()
        expected = plone_workflow_csv
        
        serializer = DefaultSerializer()
        
        output_stream = StringIO()
        serializer(info, output_stream)
        returned = output_stream.getvalue()
        
        diff = '\n'.join(difflib.unified_diff(returned.strip().splitlines(), 
                                              expected.strip().splitlines()))
                                         
        self.failIf(diff, diff)
    
class TestDeserializer(unittest.TestCase):
    
    layer = ConfigLayer
    
    def test_deserialize_complex(self):
        
        deserializer = DefaultDeserializer()
        
        input_stream = StringIO(plone_workflow_csv)
        info = deserializer(input_stream)
        
        # Basic info
        self.assertEquals('plone_workflow', info['id'])
        self.assertEquals('Community Workflow', info['title'])
        self.assertEquals('visible', info['initial_state'])
        
        # List of states
        self.assertEquals(sorted(['pending', 'private', 'published', 'visible' ]),
                          sorted([s['id'] for s in info['state_info']]))
                          
        # Permissions of a state
        pending_state_permissions = [s['permissions'] for s in info['state_info'] if s['id'] == 'pending'][0]
        pending_state_permissions = dict([(p['name'], p) for p in pending_state_permissions])
        
        self.assertEquals(False, pending_state_permissions['View']['acquired'])
        self.assertEquals(sorted(('Anonymous',)), sorted(pending_state_permissions['View']['roles']))
        
        self.assertEquals(False, pending_state_permissions['Modify portal content']['acquired'])
        self.assertEquals(sorted(('Manager', 'Reviewer')), sorted(pending_state_permissions['Modify portal content']['roles']))
        
        # List of permissions (extracted as union of all managed permissions)
        self.assertEquals(sorted(['Access contents information', 'Change portal events', 'Modify portal content', 'View']),
                          sorted(info['permissions']))
                          
        # List of transitions
        self.assertEquals(sorted(['hide', 'publish', 'reject', 'retract', 'submit', 'show']),
                          sorted([s['id'] for s in info['transition_info']]))
                          
        # List of worklists
        self.assertEquals(sorted(['reviewer-tasks']),
                          sorted([s['id'] for s in info['worklist_info']]))
        
def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestSerializer))
    suite.addTest(makeSuite(TestDeserializer))
    return suite

plone_workflow_info = \
{'description': " - Users can create content that is immediately publicly accessible. - Content can be submitted for publication by the content's creator or a Manager, which is typically done to promote events or news to the front page. - Reviewers can publish or reject content, content owners can retract their submissions. - While the content is awaiting review it is readable by anybody. - If content is published, it can only be retracted by a Manager.",
 'id': 'plone_workflow',
 'initial_state': 'visible',
 'meta_type': 'Workflow',
 'permissions': ['Access contents information',
                 'Change portal events',
                 'Modify portal content',
                 'View'],
 'script_info': [],
 'state_info': [{'description': 'Waiting to be reviewed, not editable by the owner.\n',
                 'groups': [],
                 'id': 'pending',
                 'permissions': [{'acquired': False,
                                  'name': 'Access contents information',
                                  'roles': ('Anonymous',)},
                                 {'acquired': False,
                                  'name': 'Change portal events',
                                  'roles': ('Manager', 'Reviewer')},
                                 {'acquired': False,
                                  'name': 'Modify portal content',
                                  'roles': ('Manager', 'Reviewer')},
                                 {'acquired': False,
                                  'name': 'View',
                                  'roles': ('Anonymous',)}],
                 'title': 'Pending review',
                 'transitions': ('hide', 'publish', 'reject', 'retract'),
                 'variables': []},
                {'description': 'Can only be seen and edited by the owner.\n',
                 'groups': [],
                 'id': 'private',
                 'permissions': [{'acquired': False,
                                  'name': 'Access contents information',
                                  'roles': ('Manager',
                                            'Owner',
                                            'Reader',
                                            'Editor',
                                            'Contributor')},
                                 {'acquired': False,
                                  'name': 'Change portal events',
                                  'roles': ('Manager', 'Owner', 'Editor')},
                                 {'acquired': False,
                                  'name': 'Modify portal content',
                                  'roles': ('Manager', 'Owner', 'Editor')},
                                 {'acquired': False,
                                  'name': 'View',
                                  'roles': ('Manager',
                                            'Owner',
                                            'Reader',
                                            'Editor',
                                            'Contributor')}],
                 'title': 'Private',
                 'transitions': ('show',),
                 'variables': []},
                {'description': 'Visible to everyone, not editable by the owner.\n',
                 'groups': [],
                 'id': 'published',
                 'permissions': [{'acquired': False,
                                  'name': 'Access contents information',
                                  'roles': ('Anonymous',)},
                                 {'acquired': False,
                                  'name': 'Change portal events',
                                  'roles': ('Manager',)},
                                 {'acquired': False,
                                  'name': 'Modify portal content',
                                  'roles': ('Manager',)},
                                 {'acquired': False,
                                  'name': 'View',
                                  'roles': ('Anonymous',)}],
                 'title': 'Published',
                 'transitions': ('reject', 'retract'),
                 'variables': []},
                {'description': 'Visible to everyone, but not approved by the reviewers.\n',
                 'groups': [],
                 'id': 'visible',
                 'permissions': [{'acquired': False,
                                  'name': 'Access contents information',
                                  'roles': ('Anonymous',)},
                                 {'acquired': False,
                                  'name': 'Change portal events',
                                  'roles': ('Manager', 'Owner', 'Editor')},
                                 {'acquired': False,
                                  'name': 'Modify portal content',
                                  'roles': ('Manager', 'Owner', 'Editor')},
                                 {'acquired': False,
                                  'name': 'View',
                                  'roles': ('Anonymous',)}],
                 'title': 'Public draft',
                 'transitions': ('hide', 'publish', 'submit'),
                 'variables': []}],
 'state_variable': 'review_state',
 'title': 'Community Workflow',
 'transition_info': [{'actbox_category': 'workflow',
                      'actbox_name': 'Make private',
                      'actbox_url': '%(content_url)s/content_status_modify?workflow_action=hide',
                      'after_script_name': '',
                      'description': 'Making an item private means that it will not be visible to anyone but the owner and the site administrator.\n',
                      'guard_expr': '',
                      'guard_groups': (),
                      'guard_permissions': ('Modify portal content',),
                      'guard_roles': (),
                      'id': 'hide',
                      'new_state_id': 'private',
                      'script_name': '',
                      'title': 'Member makes content private',
                      'trigger_type': 'USER',
                      'variables': []},
                     {'actbox_category': 'workflow',
                      'actbox_name': 'Publish',
                      'actbox_url': '%(content_url)s/content_status_modify?workflow_action=publish',
                      'after_script_name': '',
                      'description': 'Publishing the item makes it visible to other users.\n',
                      'guard_expr': '',
                      'guard_groups': (),
                      'guard_permissions': ('Review portal content',),
                      'guard_roles': (),
                      'id': 'publish',
                      'new_state_id': 'published',
                      'script_name': '',
                      'title': 'Reviewer publishes content',
                      'trigger_type': 'USER',
                      'variables': []},
                     {'actbox_category': 'workflow',
                      'actbox_name': 'Send back',
                      'actbox_url': '%(content_url)s/content_status_modify?workflow_action=reject',
                      'after_script_name': '',
                      'description': 'Sending the item back will return the item to the original author instead of publishing it. You should preferably include a reason for why it was not published.\n',
                      'guard_expr': '',
                      'guard_groups': (),
                      'guard_permissions': ('Review portal content',),
                      'guard_roles': (),
                      'id': 'reject',
                      'new_state_id': 'visible',
                      'script_name': '',
                      'title': 'Reviewer sends content back for re-drafting',
                      'trigger_type': 'USER',
                      'variables': []},
                     {'actbox_category': 'workflow',
                      'actbox_name': 'Retract',
                      'actbox_url': '%(content_url)s/content_status_modify?workflow_action=retract',
                      'after_script_name': '',
                      'description': 'If you submitted the item by mistake or want to perform additional edits, this will take it back.\n',
                      'guard_expr': '',
                      'guard_groups': (),
                      'guard_permissions': ('Request review',),
                      'guard_roles': (),
                      'id': 'retract',
                      'new_state_id': 'visible',
                      'script_name': '',
                      'title': 'Member retracts submission',
                      'trigger_type': 'USER',
                      'variables': []},
                     {'actbox_category': 'workflow',
                      'actbox_name': 'Promote to Draft',
                      'actbox_url': '%(content_url)s/content_status_modify?workflow_action=show',
                      'after_script_name': '',
                      'description': 'Promotes your private item to a public draft.\n',
                      'guard_expr': '',
                      'guard_groups': (),
                      'guard_permissions': ('Modify portal content',),
                      'guard_roles': (),
                      'id': 'show',
                      'new_state_id': 'visible',
                      'script_name': '',
                      'title': 'Member promotes content to public draft',
                      'trigger_type': 'USER',
                      'variables': []},
                     {'actbox_category': 'workflow',
                      'actbox_name': 'Submit for publication',
                      'actbox_url': '%(content_url)s/content_status_modify?workflow_action=submit',
                      'after_script_name': '',
                      'description': 'Puts your item in a review queue, so it can be published on the site.\n',
                      'guard_expr': '',
                      'guard_groups': (),
                      'guard_permissions': ('Request review',),
                      'guard_roles': (),
                      'id': 'submit',
                      'new_state_id': 'pending',
                      'script_name': '',
                      'title': 'Member submits content for publication',
                      'trigger_type': 'USER',
                      'variables': []}],
 'variable_info': [{'default_expr': 'transition/getId|nothing',
                    'default_type': 'string',
                    'default_value': '',
                    'description': 'Previous transition\n',
                    'for_catalog': False,
                    'for_status': True,
                    'guard_expr': '',
                    'guard_groups': (),
                    'guard_permissions': (),
                    'guard_roles': (),
                    'id': 'action',
                    'update_always': True},
                   {'default_expr': 'user/getId',
                    'default_type': 'string',
                    'default_value': '',
                    'description': 'The ID of the user who performed the last transition\n',
                    'for_catalog': False,
                    'for_status': True,
                    'guard_expr': '',
                    'guard_groups': (),
                    'guard_permissions': (),
                    'guard_roles': (),
                    'id': 'actor',
                    'update_always': True},
                   {'default_expr': "python:state_change.kwargs.get('comment', '')",
                    'default_type': 'string',
                    'default_value': '',
                    'description': 'Comment about the last transition\n',
                    'for_catalog': False,
                    'for_status': True,
                    'guard_expr': '',
                    'guard_groups': (),
                    'guard_permissions': (),
                    'guard_roles': (),
                    'id': 'comments',
                    'update_always': True},
                   {'default_expr': 'state_change/getHistory',
                    'default_type': 'string',
                    'default_value': '',
                    'description': 'Provides access to workflow history\n',
                    'for_catalog': False,
                    'for_status': False,
                    'guard_expr': '',
                    'guard_groups': (),
                    'guard_permissions': ('Request review',
                                          'Review portal content'),
                    'guard_roles': (),
                    'id': 'review_history',
                    'update_always': False},
                   {'default_expr': 'state_change/getDateTime',
                    'default_type': 'string',
                    'default_value': '',
                    'description': 'When the previous transition was performed\n',
                    'for_catalog': False,
                    'for_status': True,
                    'guard_expr': '',
                    'guard_groups': (),
                    'guard_permissions': (),
                    'guard_roles': (),
                    'id': 'time',
                    'update_always': True}],
 'worklist_info': [{'actbox_category': 'global',
                    'actbox_name': 'Pending (%(count)d)',
                    'actbox_url': '%(portal_url)s/search?review_state=pending',
                    'description': 'Reviewer tasks\n',
                    'guard_expr': '',
                    'guard_groups': (),
                    'guard_permissions': ('Review portal content',),
                    'guard_roles': (),
                    'id': 'reviewer_queue',
                    'title': '',
                    'var_match': [('review_state', 'pending')]}]}
                    
plone_workflow_csv = """\
[Workflow]
Id:,plone_workflow
Title:,Community Workflow
Description:,"- Users can create content that is immediately publicly accessible. - Content can be submitted for publication by the content's creator or a Manager, which is typically done to promote events or news to the front page. - Reviewers can publish or reject content, content owners can retract their submissions. - While the content is awaiting review it is readable by anybody. - If content is published, it can only be retracted by a Manager."
Initial state:,visible

[State]
Id:,pending
Title:,Pending review
Description:,"Waiting to be reviewed, not editable by the owner."
Transitions,"hide, publish, reject, retract"
Worklist:,Reviewer tasks
Worklist label:,Pending (%(count)d)
Worklist guard permission:,Review portal content
Worklist guard role:,
Worklist guard expression:,
Permissions,Acquire,Anonymous,Manager,Owner,Reader,Editor,Contributor,Reviewer
Access contents information,N,Y,N,N,N,N,N,N
View,N,Y,N,N,N,N,N,N
Modify portal content,N,N,Y,N,N,N,N,Y
Change portal events,N,N,Y,N,N,N,N,Y

[State]
Id:,private
Title:,Private
Description:,Can only be seen and edited by the owner.
Transitions,show
Permissions,Acquire,Anonymous,Manager,Owner,Reader,Editor,Contributor,Reviewer
Access contents information,N,N,Y,Y,Y,Y,Y,N
View,N,N,Y,Y,Y,Y,Y,N
Modify portal content,N,N,Y,Y,N,Y,N,N
Change portal events,N,N,Y,Y,N,Y,N,N

[State]
Id:,published
Title:,Published
Description:,"Visible to everyone, not editable by the owner."
Transitions,"reject, retract"
Permissions,Acquire,Anonymous,Manager,Owner,Reader,Editor,Contributor,Reviewer
Access contents information,N,Y,N,N,N,N,N,N
View,N,Y,N,N,N,N,N,N
Modify portal content,N,N,Y,N,N,N,N,N
Change portal events,N,N,Y,N,N,N,N,N

[State]
Id:,visible
Title:,Public draft
Description:,"Visible to everyone, but not approved by the reviewers."
Transitions,"hide, publish, submit"
Permissions,Acquire,Anonymous,Manager,Owner,Reader,Editor,Contributor,Reviewer
Access contents information,N,Y,N,N,N,N,N,N
View,N,Y,N,N,N,N,N,N
Modify portal content,N,N,Y,Y,N,Y,N,N
Change portal events,N,N,Y,Y,N,Y,N,N

[Transition]
Id:,hide
Target state:,private
Title:,Make private
Description:,Member makes content private
Details:,Making an item private means that it will not be visible to anyone but the owner and the site administrator.
Trigger:,User
Guard permission:,Modify portal content
Guard role:,
Guard expression:,

[Transition]
Id:,publish
Target state:,published
Title:,Publish
Description:,Reviewer publishes content
Details:,Publishing the item makes it visible to other users.
Trigger:,User
Guard permission:,Review portal content
Guard role:,
Guard expression:,

[Transition]
Id:,reject
Target state:,visible
Title:,Send back
Description:,Reviewer sends content back for re-drafting
Details:,Sending the item back will return the item to the original author instead of publishing it. You should preferably include a reason for why it was not published.
Trigger:,User
Guard permission:,Review portal content
Guard role:,
Guard expression:,

[Transition]
Id:,retract
Target state:,visible
Title:,Retract
Description:,Member retracts submission
Details:,"If you submitted the item by mistake or want to perform additional edits, this will take it back."
Trigger:,User
Guard permission:,Request review
Guard role:,
Guard expression:,

[Transition]
Id:,show
Target state:,visible
Title:,Promote to Draft
Description:,Member promotes content to public draft
Details:,Promotes your private item to a public draft.
Trigger:,User
Guard permission:,Modify portal content
Guard role:,
Guard expression:,

[Transition]
Id:,submit
Target state:,pending
Title:,Submit for publication
Description:,Member submits content for publication
Details:,"Puts your item in a review queue, so it can be published on the site."
Trigger:,User
Guard permission:,Request review
Guard role:,
Guard expression:,
"""                    