*** Settings ***
Library             SchemathesisLibrary
...                     path=${CURDIR}/../specs/empty.json

Test Template       Wrapper


*** Test Cases ***
All Tests
    Wrapper    test_case_1


*** Keywords ***
Wrapper
    [Arguments]    ${case}
    Log    Generated case for ${case.operation.label}
