*** Settings ***
Resource        runner.resource

Suite Setup     Run Suite    ${1}


*** Test Cases ***
Check Failure
    VAR    @{logs} =
    ...    *No test cases were generated: the schema contains no operations*
    Check Suite With Logs    ${LIBRARY_OUTPUT_XML}    ${logs}
