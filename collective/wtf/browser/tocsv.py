from zope.component import getUtility

from StringIO import StringIO
from Products.Five.browser import BrowserView

from collective.wtf.interfaces import ICSVWorkflowSerializer
from collective.wtf.exportimport import CSVWorkflowDefinitionConfigurator
        
class ToCSV(BrowserView):
    """Export the context workflow to CSV as a one-off
    """
    
    def __call__(self):
        
        wfdc = CSVWorkflowDefinitionConfigurator(self.context)
        info = wfdc.getWorkflowInfo(self.context.getId())
        serializer = getUtility(ICSVWorkflowSerializer)
        
        output_stream = StringIO()
        
        serializer(info, output_stream) # allow parsing error to bubble

        self.request.response.setHeader("Content-type","test/csv")
        self.request.response.setHeader("Content-disposition","attachment;filename=%s.csv" % self.context.getId())    
        return output_stream.getvalue()