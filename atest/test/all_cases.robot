*** Settings ***
Library             SchemathesisLibrary    url=http://127.0.0.1/openapi.json

Test Template       Wrapper


*** Test Cases ***
All Tests
    Wrapper    test_case_1


*** Keywords ***
Wrapper
    [Arguments]    ${case}
    Call And Validate    ${case}
