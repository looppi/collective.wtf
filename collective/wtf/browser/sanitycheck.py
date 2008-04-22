from zope.component import subscribers

from StringIO import StringIO
from Products.Five.browser import BrowserView

from plone.memoize.instance import memoize

from collective.wtf.interfaces import ISanityChecker

class SanityCheck(BrowserView):
    """Perform a number of checks on the context workflow definition
    """

    def __call__(self):
        
        # Lazy stuff - this should be put into a proper template
        
        messages = self.messages()
        out = StringIO()
        
        print >> out, "Status report for workflow:", self.context.getId()
        print >> out
        
        if messages:
            print >> out, "Found some problems."
            print >> out
            
            for message in messages:
                print >> out, message
                print >> out
        else:
            print >> out, "Nothing to report."
        
        return out.getvalue()
        
    @memoize
    def messages(self):
        """Get all messages
        """
        
        messages = []
        for checker in subscribers((self.context,), ISanityChecker):
            new_messages = checker()
            if new_messages:
                messages += new_messages
        return messages