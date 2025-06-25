*** Settings ***
Resource        runner.resource

Suite Setup     Run Suite    ${1}


*** Test Cases ***
Check Failure
    VAR    @{logs}    *Either *url* or *path* must be provided to SchemathesisLibrary*
    Check Suite With Logs    ${LIBRARY_OUTPUT_XML}    ${logs}
