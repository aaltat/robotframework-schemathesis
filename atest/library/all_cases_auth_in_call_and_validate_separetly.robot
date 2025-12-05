*** Settings ***
Library             SchemathesisLibrary    url=http://127.0.0.1/openapi.json
Variables           authentication.py

Test Template       Wrapper


*** Test Cases ***
All Tests
    Wrapper    test_case_1


*** Keywords ***
Wrapper
    [Arguments]    ${case}
    ${r} =    Call    ${case}    auth=${BASIC_AUTH_TUPLE}
    Validate Response    ${case}    ${r}    auth=${BASIC_AUTH_TUPLE}
    Log    ${r.json()}
