*** Settings ***
Resource        runner.resource
Resource        all_cases.resource

Suite Setup     Run Suite


*** Test Cases ***
Check All Cases
    Check Specific Test Logs
    ...    ${LIBRARY_OUTPUT_XML}
    ...    Converting
    ...    As Curl
    ...    number_of_tests=21
    ...    string_in_log=case to cURL
