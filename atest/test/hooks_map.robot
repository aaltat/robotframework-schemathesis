*** Settings ***
Resource        runner.resource
Resource        all_cases.resource

Suite Setup     Run Suite


*** Test Cases ***
Check All Cases
    Check Specific Test Logs
    ...    ${LIBRARY_OUTPUT_XML}
    ...    Case headers
    ...    number_of_tests=17
    ...    string_in_log='map-headers': 'I am here'
    Check Specific Test Logs
    ...    ${LIBRARY_OUTPUT_XML}
    ...    Request:
    ...    number_of_tests=17
    ...    string_in_log='map-headers': 'I am here'
