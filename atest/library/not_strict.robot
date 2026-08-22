*** Settings ***
Library             SchemathesisLibrary
...                     path=${CURDIR}/../specs/invalid_operation.json
...                     max_examples=1
...                     strict=False

Test Template       Wrapper


*** Test Cases ***
All Tests
    Wrapper    test_case_1


*** Keywords ***
Wrapper
    [Arguments]    ${case}
    Log    Generated case for ${case.operation.label}
