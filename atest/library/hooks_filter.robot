*** Settings ***
Variables           authentication.py
Library             SchemathesisLibrary
...                     url=http://127.0.0.1/openapi.json
...                     max_examples=5
...                     hook=${CURDIR}/hook_filter.py

Test Template       Wrapper


*** Test Cases ***
All Tests
    Wrapper    test_case_1


*** Keywords ***
Wrapper
    [Arguments]    ${case}
    ${r} =    Call And Validate    ${case}    auth=${BASIC_AUTH_TUPLE}
    Log    ${r.json()}
