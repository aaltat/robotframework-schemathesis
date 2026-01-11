*** Settings ***
Library             SchemathesisLibrary
...                     url=http://127.0.0.1/openapi.json
...                     max_examples=4
...                     auth=${CURDIR}/AuthExtension.py

Test Template       Wrapper


*** Test Cases ***
All Tests
    Wrapper    test_case_1


*** Keywords ***
Wrapper
    [Arguments]    ${case}
    ${response} =    Call    ${case}
    Validate Response    ${case}    ${response}
    Log    ${response.json()}
