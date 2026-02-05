*** Settings ***
Resource        runner.resource
Resource        all_cases.resource

Suite Setup     Run Suite


*** Test Cases ***
Check All Cases
    Check Specific Test Logs
    ...    ${LIBRARY_OUTPUT_XML}
    ...    Using provided session
    ...    number_of_tests=17
    ...    string_in_log=Using provided session for the request.
