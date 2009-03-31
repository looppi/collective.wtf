===============
collective.wtf
===============

 by Martin Aspeli <optilude@gmail.com>
 
This package contains tools for working with DC Workflow definitions via
spreadsheets (or rather, CSV format) as well as debugging aids to make it
easier to work with security and workflow in Zope 2 and Plone.

It consists of:

 - A GenericSetup exporter that can dump a workflow definition to a CSV file
 - A GenericSetup importer that can create a workflow definition from a CSV
   file
 - An in-browser tool to sanity-check a workflow
 - A browser view to dump a workflow in the site to CSV as a one-off
 - A browser view to show the roles of a user in a given context
 - Utility functions to trigger automatic transitions on an object, as well as
    on its parent.
 
CSV import/export
=================

Please note that the CSV format is not completely equivalent to the standard 
XML-based GenericSetup format to import/export workflow definitions. If you
require the full power of DCWorkflow, you should continue to use the XML
based format. This is not (just) due to laziness - the CSV format has been 
simplified to make common operations easy.

For an example CSV file, see
 
    collective/wtf/tests/profiles/testing/test_wf.csv.
    
To be imported as part of a GenericSetup extension profile, a file like this
would normally go in

    profiles/default/workflow_csv/wf_name.csv 
    
where wf_name is the name of the workflow in portal_workflow.

Note that if a full workflow definition does exist (e.g. in 
profiles/default/workflows/my_workflow/definition.xml), the CSV importer will
*not* attempt to run an import, so as not to conflict or overwrite changes.

To download a workflow definition in CSV format as a one-off, type a URL like
this into your browser:

 http://localhost:8080/Plone/portal_workflow/my_workflow/@@to-csv

Here, "Plone" is the name of the Plone instance and "my_workflow" is the name
of your workflow definition. You will be asked to download a CSV file.

Workflow sanity checker
=======================

To invoke the sanity checker, type a URL like this into your browser:

 http://localhost:8080/Plone/portal_workflow/my_workflow/@@sanity-check
 
Again, "Plone" is the name of the Plone instance and "my_workflow" is the name
of the workflow definition. The output will be written to the browser window
in plain text.

Other debugging aids
====================

To view the current roles of a given user in a given context, type a URL like
this into your browser when logged in as a Manager user:

 http://localhost:8080/Plone/context/@@display-roles-in-context?user=<user>
 
Again, "Plone" is the name of the Plone instance. "context" could be any 
object. <user> should be replaced by the login name/id of the user you 
want to fetch roles for. The output will be written to the browser window in
plain text.

CSV file specification
======================

This section details the CSV file format.

General
-------

The CSV file format generally relies on key-value pairs, where keys are in
the first column (A) and values in the second column (B). Key names are not
case sensitive, may substitute hyphens for spaces, and may optionally contain
a trailing colon. For example, the following are all equivalent::

  Some key:,some_value
  some key:,some_value
  some-key , some_value

The file is sub-divided into sections. A section begins with a row containing
the section name in square brackets, and ends with at least one blank row.
For example::

  [SomeSection]
  Some key:,some_value
  Some other key:,another_value
  
  [AnotherSection]
  ...
  
The various sections are listed below, in more detail.

The [Workflow] section
----------------------

This is generally the first section in the file. It contains information
about the workflow as a whole, with the following keys. Keys marked with a
* are required.

  Id* -- The name of the workflow as it will be installed in portal_workflow.

  Initial state* -- The name of the initial state of the workflow. Must match
    the id of a [State] section elsewhere in the file.
    
  Title -- A human-friendly title for the workflow.
  
  Description -- A human-friendly description for the workflow.

For example::

  [Workflow]
  Id:,test_workflow
  Title:,Test workflow
  Description:,Description of workflow
  Initial state:,state_one
  
The [State] section
-------------------

This section defines a single workflow state. It must end with a permissions
table - see below.

 Id* -- A unique name for the state.
 
 Title* -- A human-friendly title.
 
 Description -- A human-friendly description.
 
 Transitions -- A comma-separated list of transitions. Note that this should
    be limited to a single cell. Hence, you will need double quotes around
    the list, e.g. "transition_1, transition_2". Each transition listed
    must match the id of a [Transition] section elsewhere in the file.
 
 Worklist -- The name of a worklist for objects in this state, if one is
    required.
 
 Worklist label -- A human-friendly label for the worklist.
  
 Worklist guard permission -- The name of a permission used to guard the
    worklist, if required.
 
 Worklist guard expression -- A TALES expression used to guard the worklist,
    if required.
 
 Worklist guard role -- The name of a role used to guard the workflist, if
    required.

For example::

  [State]
  Id:,state_one
  Title:,State one
  Description:,Description of state one
  Transitions:,"to_state_two,to_state_three"
  Worklist:,State one worklist
  Worklist label:,Worklist stuff goes here
  Worklist guard permission:,Review portal content
  Worklist guard expression:,python:True==True
  Worklist guard role:,Manager
  Permissions,                  Acquire,  Manager, Member, Owner
  View,                         Y,        Y,       N,      Y
  Access contents information,  Y,        Y,       N,      Y
  Modify portal content,        N,        Y,       N,      N

The permissions table
---------------------

At the end of a [State] section, before the blank line that signals the end
of that section, there must be a table of permissions for this state. The
table may look like this::

  Permissions,                  Acquire,  Manager, Member, Owner
  View,                         Y,        Y,       N,      Y
  Access contents information,  Y,        Y,       N,      Y
  Modify portal content,        N,        Y,       N,      N
  
Note that the additional whitespace here is purely for readability, and is
optional.

The permissions table is created by having the pseudo-key 'Permissions' in
column A. Column B is used to indicate whether a given permission is acquired
from the parent object or not. By convention, the header row should contain
the word 'Acquire' here. Subsequent rows should contain role names.

Underneath the header row, the first column should contain the names of
permissions. Subsequent columns indicate whether the given role has the
given permission in this workflow state. A case-insensitive value of 'Y', 
'*', 'X' or 'Yes' indicates true. Any other value (including blanks, 'N' or
'No') indicates false.

The [Transition] section
------------------------

This section defines a transition between two states. It may contain the
following keys:

  Id* -- A unique identifier for the transition
  
  Title -- A human-friendly title for the transition.

  Description -- A human-friendly description for the transition.

  URL -- A string containing a URL that will be used when the user clicks
    the transition in the workflow menu. May contain the special variables
    %(portal_url)s, %(folder_url)s, %(content_url)s and %(user_id)s. If not
    given, the default view will be used.

  Target state -- The state that the workflow should move to after this
    transition has been executed. If omitted, the transition will not cause
    a state change. If included, it must match the id of a [State] section
    defined elsewhere in the file.
  
  Trigger -- One of 'User' or 'Automatic'. Defaults to 'User'. An automatic
    transition is one which is run automatically when the workflow enters a
    state for which the automatic transition is a valid exit transition.
    Automatic transitions are often used with transition guards to
    automatically advance the workflow in certain situations, and/or with
    transition scripts that execute on the automatic transition.
    
  Guard permission -- The name of a permission that is required before this
    transition is made available.
  
  Guard expression -- A TALES expression that must be true before this
    transition is made available.
  
  Guard role -- The name of a role that the current user must have before
    this transition is made available.
  
  Script before -- A script to execute before the transition effects a state
    change. This may either contain a simple string, in which case it must
    match the id of a [Script] section elsewhere in the file, or a dotted
    name to an external method, e.g. 
    'my.product.Extensions.script_name.function_name', where 'my.product' is
    the name of a product that contains an Extensions/ folder, 'script_name'
    is the name of a .py file in that Extensions/ folder, and 'function_name'
    is the name of a function in that .py file. The function must take two
    parameters: self, and a state_change, a StateChangeInfo object. In this
    case, the importer will create a new External Method with the appropriate
    module ('my.product.script_name') and function ('function_name'), give it
    and id based on the script and function name (in this case,
    'script_name.function_name'), and set this as the script before.
  
  Script after -- A script to execute after the transition effects a state
    change. This may contain the same values as Script before.
 
For example::

  [Transition]
  Id:,to_state_one
  Title:,Make it state one
  Description:,Make it go to state one
  Target state:,state_one
  Trigger:,User
  Guard permission:,Modify portal content,View
  Guard expression:,python:True==True
  Guard role:,Manager
  Script before:,shared_script
  Script after:,collective.wtf.Extensions.test_scripts.inline_test_one
  
The [Script] section
--------------------

This may be used to define a script explicitly. Only external method scripts
are supported. Note that single-use external methods can be defined "inline"
using the notation described under 'The [Transition] section' above.

  Id* -- The id of the script
  
  Type* -- Should be 'External Method'. In the future, other types of script
    may be supported.
    
  Module* -- The module where the external method is defined. Note that this
    should not contain the 'Extensions' directory.
    
  Function* -- The name of the function to execute when the external method
    is run.

For example::

  [Script]
  Id:,shared_script
  Type:,External Method
  Module:, collective.wtf.test_scripts
  Function:,script_section_test
