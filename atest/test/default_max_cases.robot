*** Settings ***
Resource        runner.resource
Resource        all_cases.resource

Suite Setup     Run Suite


*** Test Cases ***
Check All Cases
    Check Specific Test Logs
    ...    ${LIBRARY_OUTPUT_XML}
    ...    Case headers
    ...    number_of_tests=401
    ...    string_in_log=path parameters
