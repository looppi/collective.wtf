import os.path
from StringIO import StringIO

from zope.component import queryMultiAdapter
from zope.component import getUtility

from AccessControl import ClassSecurityInfo
from Globals import InitializeClass

from Products.GenericSetup.interfaces import IBody
from Products.GenericSetup.interfaces import ISetupEnviron
from Products.GenericSetup.utils import BodyAdapterBase

from Products.DCWorkflow.interfaces import IDCWorkflowDefinition
from Products.DCWorkflow.exportimport import WorkflowDefinitionConfigurator
from Products.DCWorkflow.exportimport import _initDCWorkflow

from zope.component import adapts

from collective.wtf.interfaces import ParsingError
from collective.wtf.interfaces import ICSVWorkflowSerializer
from collective.wtf.interfaces import ICSVWorkflowDeserializer 

import Products

class CSVWorkflowDefinitionConfigurator(WorkflowDefinitionConfigurator):
    """Cheat by borrowing a lot of logic from the DCWorkflow handler
    """
    
    security = ClassSecurityInfo()
    
    def __init__(self, obj, info=None):
        super(CSVWorkflowDefinitionConfigurator, self).__init__(obj)
        self.info = info
        
    def generateWorkflowXML(self):
        """ Pseudo API.
        """
        return self._workflowConfig(workflow_id=self._obj.getId())
        
    security.declarePublic('getWorkflowInfo')
    def getWorkflowInfo(self, workflow_id ):
        if self.info is not None:
            return self.info
        else:
            
            workflow = self._obj
            workflow_info = {
                    'id'          : workflow_id, 
                    'meta_type'   : workflow.meta_type,
                    'title'       : workflow.title_or_id(),
                    'description' : workflow.description
                }

            if IDCWorkflowDefinition.providedBy(workflow):
                self._extractDCWorkflowInfo(workflow, workflow_info)

            return workflow_info

InitializeClass(CSVWorkflowDefinitionConfigurator)

class DCWorkflowDefinitionBodyAdapter(BodyAdapterBase):
    """Body im- and exporter for DCWorkflowDefinition in CSV format.
    """

    adapts(IDCWorkflowDefinition, ISetupEnviron)
    
    def _exportBody(self):
        """Return the most commonly used aspects of a workflow as a CSV
        file string.
        """
        
        logger = self.environ.getLogger('workflow-csv')
        wfdc = CSVWorkflowDefinitionConfigurator(self.context)
        info = wfdc.getWorkflowInfo(self.context.getId())
        serializer = getUtility(ICSVWorkflowSerializer)
        
        output_stream = StringIO()
        
        try:
            serializer(info, output_stream)
        except ParsingError, p:
            logger.error("Error parsing %s: %s" % (self.filename, str(p)))
            raise p
            
        return output_stream.getvalue()

    def _importBody(self, body):
        """Import the object from the file body.
        """
        
        logger = self.environ.getLogger('workflow-csv')
        
        if isinstance(body, dict):
            info = body
        else:
            input_stream = StringIO(body)
            deserializer = getUtility(ICSVWorkflowDeserializer)
        
            info = {}
        
            try:
                info = deserializer(input_stream)
            except ParsingError, p:
                logger.error("Error parsing %s: %s" % (self.filename, str(p)))
                raise p
        
        # cheat :)
        
        encoding = 'utf-8'
        wfdc = CSVWorkflowDefinitionConfigurator(self.context, info=info)
        xml_body = wfdc.__of__(self.context).generateWorkflowXML()
        
        try: # CMF 2.1 / Plone 3
            ( workflow_id
            , title
            , state_variable
            , initial_state
            , states
            , transitions
            , variables
            , worklists
            , permissions
            , scripts
            , description
            ) = wfdc.parseWorkflowXML(xml_body, encoding)
        
            _initDCWorkflow( self.context
                           , title
                           , description
                           , state_variable
                           , initial_state
                           , states
                           , transitions
                           , variables
                           , worklists
                           , permissions
                           , scripts
                           , self.environ
                           )
        except (ValueError, TypeError,): # CMF 2.2 / Plone 4
            ( workflow_id
            , title
            , state_variable
            , initial_state
            , states
            , transitions
            , variables
            , worklists
            , permissions
            , scripts
            , description
            , manager_bypass
            , creation_guard
            ) = wfdc.parseWorkflowXML(xml_body, encoding)
            
            _initDCWorkflow( self.context
                           , title
                           , description
                           , manager_bypass
                           , creation_guard
                           , state_variable
                           , initial_state
                           , states
                           , transitions
                           , variables
                           , worklists
                           , permissions
                           , scripts
                           , self.environ
                           )

    body = property(_exportBody, _importBody)

def importCSVWorkflow(context):
    """Import portlet managers and portlets
    """
    
    site = context.getSite()
    logger = context.getLogger('workflow-csv')
    
    portal_workflow = getattr(site, 'portal_workflow', None)
    
    if portal_workflow is None:
        return
    
    csv_dir = context.listDirectory('workflow_csv')
    if not csv_dir:
        return
    else:
        csv_dir = set(csv_dir)
    
    xml_dir = context.listDirectory('workflows')
    if not xml_dir:
        xml_dir = set()
    
    for csv_filename in csv_dir:
        
        if not csv_filename.endswith('.csv'):
            continue
        
        wf_name = str(csv_filename[:-4]) # yes, this is evil
        xml_filename = "%s.xml" % wf_name
        
        if xml_filename in xml_dir:
            logger.warn('Skipping CSV workflow definition in %s since %s exists.' % (csv_filename, xml_filename))
            continue
        
        filename = os.path.join("workflow_csv", csv_filename)
        body = context.readDataFile(filename)
        
        if body is None:
            return
        
        input_stream = StringIO(body)
        deserializer = getUtility(ICSVWorkflowDeserializer)
        
        info = {}
        
        try:
            info = deserializer(input_stream)
        except ParsingError, p:
            logger.error("Error parsing %s: %s" % (filename, str(p)))
            raise p
        
        wf = None
        
        if wf_name in portal_workflow.objectIds():
            logger.info('Updating existing workflow definition %s.' % wf_name)
            wf = portal_workflow[wf_name]
        else:
            logger.info('Creating workflow definition %s using standard workflows.' % wf_name)
            wf_name = info['id']
            meta_type = info.get('meta_type', 'Workflow')
            for mt_info in Products.meta_types:
                if mt_info['name'] == meta_type:
                    portal_workflow._setObject(wf_name, mt_info['instance'](wf_name))
                    break
            
            wf = portal_workflow[wf_name]
        
        importer = queryMultiAdapter((wf, context), IBody, name=u'collective.wtf')
        importer.filename = filename # for error reporting
        importer.body = info

def exportCSVWorkflow(context):
    """Export portlet managers and portlets
    """
    site = context.getSite()
    portal_workflow = getattr(site, 'portal_workflow', None)
    
    if portal_workflow is None:
        return
    
    for wf in portal_workflow.objectValues():
        exporter = queryMultiAdapter((wf, context), IBody, name=u'collective.wtf')
        
        if not os.path.exists('workflow_csv'):
            os.mkdir('workflow_csv')
        
        filename = os.path.join("workflow_csv", "%s.csv" % wf.getId())
        body = exporter.body
        if body is not None:
            context.writeDataFile(filename, body, 'text/csv')