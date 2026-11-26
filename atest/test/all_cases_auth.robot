*** Settings ***
Resource       runner.resource
Resource       all_cases.resource

Suite Setup    Run Suite


*** Variables ***
# Base64 of joulu:pukki, which AuthExtension.py sends
${CREDENTIALS}    am91bHU6cHVra2k=


*** Test Cases ***
Check All Cases
    ${test_description} =    Get All Cases Test Description
    Check Suite    ${LIBRARY_OUTPUT_XML}    ${test_description}

Credentials Are Not In The Output
    ${output} =    Get File    ${LIBRARY_OUTPUT_XML}
    ${count} =    Get Count    ${output}    ${CREDENTIALS}
    Should Be Equal As Integers    ${count}    0
