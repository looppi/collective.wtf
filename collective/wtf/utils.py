from Products.CMFCore.utils import getToolByName
from Acquisition import aq_parent, aq_inner

def trigger_automatic_transitions(context, event=None):
    """Trigger automatic transitions for all workflows associated with the
    given object, going through teh workflow chain in reverse order. This
    allows a transition in a workflow lower down the chain to cause another
    transition in a workflow higher up the chain.
    
    It is possible to register this for the IActionSuceededEvent object event
    so that it takes place automatically on each transition for a given object
    type:
    
      <subscriber
          for=".interfaces.IMyType
               Products.CMFCore.interfaces.IActionSucceededEvent"
          handler="collective.wtf.utils.trigger_automatic_transitions"
          />
    """
    wtool = getToolByName(context, 'portal_workflow')
    chain = list(wtool.getChainFor(context))
    chain.reverse()
    changed = False
    for wfid in chain:
        workflow = wtool.getWorkflowById(wfid)
        sdef = workflow._getWorkflowStateOf(context)
        if sdef is None:
            continue
        tdef = workflow._findAutomaticTransition(context, sdef)
        if tdef is None:
            continue
        changed = True
        workflow._changeStateOf(context, tdef)
    if changed:
        wtool._reindexWorkflowVariables(context)

def trigger_automatic_transitions_in_parent(context, event=None):
    """Trigger automatic transitions in the parent of context.
    
    It is possible to register this for the IActionSuceededEvent object event
    so that it takes place automatically on each transition for a given object
    type:
    
      <subscriber
          for=".interfaces.IMyType
               Products.CMFCore.interfaces.IActionSucceededEvent"
          handler="collective.wtf.utils.trigger_automatic_transitions_in_parent"
          />
    """
    parent = aq_parent(aq_inner(context))
    trigger_automatic_transitions(parent, event)