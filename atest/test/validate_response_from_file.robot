*** Settings ***
Resource       runner.resource

Suite Setup    Run Suite


*** Test Cases ***
Check All Cases
    Check Specific Test Logs
    ...    ${LIBRARY_OUTPUT_XML}
    ...    Response validation passed
    ...    kw_name=Validate Response
    ...    number_of_tests=21
    ...    string_in_log=Response validation passed.
