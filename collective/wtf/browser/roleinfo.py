from StringIO import StringIO
from Acquisition import aq_inner

from Products.Five.browser import BrowserView
from Products.CMFCore.utils import getToolByName

class RoleInfo(BrowserView):
    """Display information about a user's roles
    """

    def __call__(self):
        
        # Lazy stuff - this should be put into a proper template
        
        out = StringIO()

        context = aq_inner(self.context)
        portal_membership = getToolByName(context, 'portal_membership')
        
        userid = self.request.get('user', None)
        if userid:
            member = portal_membership.getMemberById(userid)
        else:
            member = portal_membership.getAuthenticatedMember()
        
        print >> out, "Roles for user", member.getId(), "in context", context.absolute_url()
        print >> out
        print >> out, member.getRolesInContext(context)
        
        print >> out
        print >> out, "Use %s/%s?user=<name> to check roles for a particular user" % (context.absolute_url(), self.__name__)
        
        return out.getvalue()
