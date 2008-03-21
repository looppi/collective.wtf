from zope.interface import Interface, Attribute

class ParsingError(Exception):
    """Raised when a CSV file cannot be parsed.
    """

class ICSVWorkflowSerializer(Interface):
    """Export workflow to CSV
    """
    
    def __call__(info, output_stream, config_variant=u""):
        """Write the workflow info dict to the output stream.
        """
    
class ICSVWorkflowDeserializer(Interface):
    """Import workflow from CSV
    """
    
    def __call__(input_stream, config_variant=u""):
        """Read CSV from the given input stream and return a workflow
        info dict.
        """

class ICSVWorkflowConfig(Interface):
    """Configuration options
    """
    
    known_roles = Attribute("A list of known roles in their preferred order")
    known_permission = Attribute("A list of known permissions in their preferred order")
    
    # remember to call .copy() when using these!
    
    info_template = Attribute("A template for the info dict")
    state_template = Attribute("A template a state dict inside info['state_info']")
    state_permission_template = Attribute("A template a permission dict inside info['state_info'][a_state]['permissions']")
    transition_template = Attribute("A template a transition dict inside info['transition_info']")
    worklist_template = Attribute("A template a worklist dict inside info['workflist_info']")