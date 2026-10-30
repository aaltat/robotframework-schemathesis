*** Settings ***
Resource       runner.resource

Suite Setup    Run Suite


*** Test Cases ***
Auth Provider Reaches The Server
    Check Specific Test Logs
    ...    ${LIBRARY_OUTPUT_XML}
    ...    Request: GET http://127.0.0.1/user/
    ...    kw_name=Call And Validate
    ...    number_of_tests=5
    ...    string_in_log='Authorization': '[Filtered]'
