from Products.Five.browser import BrowserView

class SanityChecker(BrowserView):
    """Perform a number of checks on the context workflow definition
    """

    def core_permissions(self):
        pass
    
    def view_vs_access(self):
        pass
        
    def owner_vs_reader(self):
        pass
        
    def owner_vs_editor(self):
        pass
        
    def owner_vs_contributor(self):
        pass
        
    def state_variable(self):
        pass