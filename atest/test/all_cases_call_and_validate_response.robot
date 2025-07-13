*** Settings ***
Resource        runner.resource
Resource        all_cases.resource

Suite Setup     Run Suite


*** Test Cases ***
Check All Cases
    ${test_description}=    Get All Cases Test Description Separate    4
    Check Suite    ${LIBRARY_OUTPUT_XML}    ${test_description}
