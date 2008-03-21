import os.path
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
from collective.wtf import serializer


class DCWorkflowDefinitionBodyAdapter(BodyAdapterBase):
    """Body im- and exporter for DCWorkflowDefinition in CSV format.
    """

    adapts(IDCWorkflowDefinition, ISetupEnviron)
    
    def _exportBody(self):
        """Return the most commonly used aspects of a workflow as a CSV
        file string.
        """
        
        wfdc = WorkflowDefinitionConfigurator(self.context)
        info = wfdc.getWorkflowInfo(self.context.getId())
        
        output = StringIO()
        serializer.write_csv(info, output)
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