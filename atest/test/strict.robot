*** Settings ***
Resource        runner.resource

Suite Setup     Run Suite    ${1}


*** Test Cases ***
Check Failure
    VAR    @{logs} =
    ...    *Failed to parse 1 of 2 operations in the schema*GET /bad*Use strict=False to skip operations that can not be parsed*
    Check Suite With Logs    ${LIBRARY_OUTPUT_XML}    ${logs}
