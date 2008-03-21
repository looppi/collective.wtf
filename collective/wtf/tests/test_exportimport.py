import time
import transaction
import difflib

from zope.component import getMultiAdapter

from zope.component import getSiteManager

from Products.Five import zcml
from Products.Five import fiveconfigure

from Products.GenericSetup.interfaces import IBody
from Products.GenericSetup.context import TarballExportContext

from Products.PloneTestCase.PloneTestCase import PloneTestCase
from Products.PloneTestCase.PloneTestCase import setupPloneSite
from Products.PloneTestCase.layer import PloneSite
from Testing import ZopeTestCase

setupPloneSite()

zcml_string = """\
<configure xmlns="http://namespaces.zope.org/zope"
           xmlns:browser="http://namespaces.zope.org/browser"
           xmlns:plone="http://namespaces.plone.org/plone"
           xmlns:gs="http://namespaces.zope.org/genericsetup"
           package="collective.wtf">

    <gs:registerProfile
        name="testing"
        title="collective.wtf testing"
        description="Used for testing only" 
        directory="tests/profiles/testing"
        for="Products.CMFCore.interfaces.ISiteRoot"
        provides="Products.GenericSetup.interfaces.EXTENSION"
        />
        
</configure>
"""

class ZCMLLayer(PloneSite):
    
    @classmethod
    def setUp(cls):
        fiveconfigure.debug_mode = True
        zcml.load_string(zcml_string)
        import collective.wtf
        zcml.load_config('configure.zcml', collective.wtf)
        fiveconfigure.debug_mode = False

    @classmethod
    def tearDown(cls):
        pass
        
class GSLayer(ZCMLLayer):
    
    @classmethod
    def setUp(cls):
        app = ZopeTestCase.app()
        portal = app.plone
        
        portal_setup = portal.portal_setup
        # wait a bit or we get duplicate ids on import
        time.sleep(1)
        portal_setup.runAllImportStepsFromProfile('profile-collective.wtf:testing')
        
        transaction.commit()
        ZopeTestCase.close(app)

    @classmethod
    def tearDown(cls):
        pass

class TestGenericSetup(PloneTestCase):
    """
    """
    
    layer = GSLayer
    
    def test_export(self):
        wf = self.portal.portal_workflow.plone_workflow
        context = TarballExportContext(self.portal.portal_setup)
        handler = getMultiAdapter((wf, context), IBody, name=u'collective.wtf')
        
        expected = """\
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
Worklist:,"Reviewer tasks
"
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
Description:,Making an item private means that it will not be visible to anyone but the owner and the site administrator.
Trigger:,User
Script before:,
Script after:,
Guard permission:,Modify portal content
Guard role:,
Guard expression:,

[Transition]
Id:,publish
Target state:,published
Title:,Publish
Description:,Publishing the item makes it visible to other users.
Trigger:,User
Script before:,
Script after:,
Guard permission:,Review portal content
Guard role:,
Guard expression:,

[Transition]
Id:,reject
Target state:,visible
Title:,Send back
Description:,Sending the item back will return the item to the original author instead of publishing it. You should preferably include a reason for why it was not published.
Trigger:,User
Script before:,
Script after:,
Guard permission:,Review portal content
Guard role:,
Guard expression:,

[Transition]
Id:,retract
Target state:,visible
Title:,Retract
Description:,"If you submitted the item by mistake or want to perform additional edits, this will take it back."
Trigger:,User
Script before:,
Script after:,
Guard permission:,Request review
Guard role:,
Guard expression:,

[Transition]
Id:,show
Target state:,visible
Title:,Promote to Draft
Description:,Promotes your private item to a public draft.
Trigger:,User
Script before:,
Script after:,
Guard permission:,Modify portal content
Guard role:,
Guard expression:,

[Transition]
Id:,submit
Target state:,pending
Title:,Submit for publication
Description:,"Puts your item in a review queue, so it can be published on the site."
Trigger:,User
Script before:,
Script after:,
Guard permission:,Request review
Guard role:,
Guard expression:,
"""

        body = handler.body
        
        diff = '\n'.join(list(difflib.unified_diff(body.strip().splitlines(), expected.strip().splitlines())))
                                         
        self.failIf(diff, diff)
        
def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestGenericSetup))
    return suite
