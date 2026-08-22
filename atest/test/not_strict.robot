*** Settings ***
Resource        runner.resource

Suite Setup     Run Suite


*** Test Cases ***
Check Only Operations That Can Be Parsed Are Tested
    VAR    &{tests} =    GET=1
    Check Test Names And Counts    ${LIBRARY_OUTPUT_XML}    1    1    ${tests}

Check Warning About Operations That Can Not Be Parsed
    VAR    @{logs} =
    ...    *Failed to parse these parts of the schema*GET /bad*Parts of the schema that can not be parsed are not tested*
    Check Suite With Logs    ${LIBRARY_OUTPUT_XML}    ${logs}
