*** Settings ***
Resource       runner.resource

Suite Setup    Run Suite


*** Test Cases ***
Check All Cases
    Check Specific Test Logs
    ...    ${LIBRARY_OUTPUT_XML}
    ...    Request:
    ...    number_of_tests=21
    ...    string_in_log=https://127.0.0.1:8443/
