*** Settings ***
Library          SchemathesisLibrary    url=http://127.0.0.1/broken/openapi.json    max_examples=30

Test Template    Wrapper


*** Test Cases ***
All Tests
    Wrapper    test_case_1


*** Keywords ***
Wrapper
    [Arguments]    ${case}
    Call And Validate    ${case}
