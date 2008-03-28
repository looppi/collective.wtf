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
 - A browser view to dump a workflow in the site to CSV as a one-off
 
Note that the CSV format is not completely equivalent to the standard 
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

To invoke the sanity checker, type a URL like this into your browser:

 http://localhost:8080/Plone/portal_workflow/my_workflow/@@sanity-check
 
Again, "Plone" is the name of the PLone instance and "my_workflow" is the name
of the workflow definition. The output will be written to the browser window
in plain text.
