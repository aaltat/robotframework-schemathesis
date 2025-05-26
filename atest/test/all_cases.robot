*** Settings ***
Library             SchemathesisLibrary

Test Template       Wrapper


*** Test Cases ***
All Tests
    Wrapper    test_case_1


*** Keywords ***
Wrapper
    [Arguments]    ${case}
    Run And Validate    ${case}
