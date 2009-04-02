import time
import transaction
import difflib

from zope.component import getMultiAdapter

from Products.Five import zcml
from Products.Five import fiveconfigure

from Products.GenericSetup.interfaces import IBody
from Products.GenericSetup.context import TarballExportContext

from Products.PloneTestCase.PloneTestCase import PloneTestCase
from Products.PloneTestCase.PloneTestCase import setupPloneSite
from Products.PloneTestCase.layer import PloneSite
from Testing import ZopeTestCase

from collective.wtf.tests.test_parsing import plone_workflow_csv

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
    
    def test_import(self):
        self.failUnless('test_wf' in self.portal.portal_workflow.objectIds())
        self.assertEquals('State one', self.portal.portal_workflow.test_wf.states.state_one.title)
        self.assertEquals('Make it state two', self.portal.portal_workflow.test_wf.transitions.to_state_two.actbox_name)
        
        self.failUnless('shared_script' in self.portal.portal_workflow.test_wf.scripts.objectIds())
        self.failUnless('test_scripts.inline_test_one' in self.portal.portal_workflow.test_wf.scripts.objectIds())
        self.failUnless('test_scripts.inline_test_two' in self.portal.portal_workflow.test_wf.scripts.objectIds())
    
    def test_export_standard(self):
        wf = self.portal.portal_workflow.plone_workflow
        context = TarballExportContext(self.portal.portal_setup)
        handler = getMultiAdapter((wf, context), IBody, name=u'collective.wtf')
        
        expected = plone_workflow_csv

        body = handler.body
        
        diff = '\n'.join(list(difflib.unified_diff(body.strip().splitlines(), expected.strip().splitlines())))
                                         
        self.failIf(diff, diff)

    def test_export_imported(self):
        wf = self.portal.portal_workflow.test_wf
        context = TarballExportContext(self.portal.portal_setup)
        handler = getMultiAdapter((wf, context), IBody, name=u'collective.wtf')
        
        expected = """\
[Workflow]
Id:,test_wf
Title:,Test workflow
Description:,Description of workflow
Initial state:,state_one
Type:,Workflow

[State]
Id:,state_one
Title:,State one
Description:,Description of state one
Transitions,"to_state_two, to_state_three"
Worklist:,State one worklist
Worklist label:,Worklist stuff goes here
Worklist guard permission:,Review portal content
Worklist guard role:,Manager
Worklist guard expression:,python:True==True
Permissions,Acquire,Anonymous,Manager,Owner,Reader,Editor,Contributor,Member
Access contents information,Y,N,Y,Y,N,N,N,N
View,Y,N,Y,Y,N,N,N,Y
Modify portal content,N,N,Y,N,N,N,N,N

[State]
Id:,state_three
Title:,State three
Description:,Description of state three
Transitions,to_state_one
Permissions,Acquire,Anonymous,Manager,Owner,Reader,Editor,Contributor,Member
Access contents information,N,N,Y,Y,N,N,N,N
View,N,N,Y,Y,N,N,N,N
Modify portal content,N,N,N,N,N,N,N,N

[State]
Id:,state_two
Title:,State two
Description:,Description of state two
Transitions,to_state_three
Permissions,Acquire,Anonymous,Manager,Owner,Reader,Editor,Contributor,Member
Access contents information,Y,N,Y,Y,N,N,N,N
View,Y,N,Y,Y,N,N,N,N
Modify portal content,N,N,Y,N,N,N,N,N

[Transition]
Id:,to_state_one
Title:,Make it state one
Description:,Make it go to state one
Target state:,state_one
URL:,%(portal_url)s/change_to_state_one
Trigger:,User
Guard permission:,Modify portal content
Guard role:,Manager
Guard expression:,python:True==True
Script before:,shared_script
Script after:,test_scripts.inline_test_one

[Transition]
Id:,to_state_three
Title:,Make it state three
Description:,Make it go to state one
Target state:,state_three
Trigger:,User

[Transition]
Id:,to_state_two
Title:,Make it state two
Description:,Make it go to state one
Target state:,state_two
Trigger:,User
Guard permission:,Modify portal content
Script before:,test_scripts.inline_test_two

[Script]
Id:,shared_script
Type:,External Method
Module:,collective.wtf.test_scripts
Function:,script_section_test

[Script]
Id:,test_scripts.inline_test_one
Type:,External Method
Module:,collective.wtf.test_scripts
Function:,inline_test_one

[Script]
Id:,test_scripts.inline_test_two
Type:,External Method
Module:,collective.wtf.test_scripts
Function:,inline_test_two

"""

        body = handler.body
        
        diff = '\n'.join(list(difflib.unified_diff(body.strip().splitlines(), expected.strip().splitlines())))
                                         
        self.failIf(diff, diff)
        
def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestGenericSetup))
    return suite
