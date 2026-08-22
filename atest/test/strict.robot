*** Settings ***
Resource        runner.resource

Suite Setup     Run Suite    ${1}


*** Test Cases ***
Check Failure
    VAR    @{logs} =
    ...    *Failed to parse these parts of the schema*GET /bad*Use strict=False to skip parts that can not be parsed*
    Check Suite With Logs    ${LIBRARY_OUTPUT_XML}    ${logs}
