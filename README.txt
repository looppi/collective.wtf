===============
collective.wtf
===============

 by Martin Aspeli <optilude@gmail.com>
 
This package contains tools for working with DC Workflow definitions via
spreadsheets (or rather, CSV format).

It consists of:

 - A GenericSetup exporter that can dump a workflow definition to a CSV file
 - A GenericSetup importer that can create a workflow definition from a CSV
   file
 - An in-browser tool to sanity-check a workflow
 
Note that the CSV format is not completely equivalent to the standard 
XML-based GenericSetup format to import/export workflow definitions. If you
require the full power of DCWorkflow, you should continue to use the XML
based format. This is not (just) due to laziness - the CSV format has been 
simplified to make common operations easy.

For an example CSV file, see
 
    collective/wtf/tests/profiles/testing/test_wf.csv.
    
A file like this would normally go in

    profiles/default/workflow_csv/wf_name.csv 
    
where wf_name is the name of the workflow in portal_workflow. Note that you still need at least a workflows.xml to initialise the workflow definition.

Also note that if a full workflow definition does exist (e.g. in 
profiles/default/workflows/my_workflow/definition.xml), the CSV importer will
*not* attempt to run an import, so as not to conflict or overwrite changes.

To invoke the sanity checker, type a URL like this into your browser:

 http://localhost:8080/Plone/portal_workflow/my_workflow/@@sanity-check
 
Here, "Plone" is the name of the Plone instance and "my_workflow" is the name
of your workflow definition. The output will be written to the browser window
in plain text.