*** Settings ***
Library          SchemathesisLibrary
...                  url=https://127.0.0.1:8443/openapi.json
...                  max_examples=1

Test Template    Wrapper


*** Test Cases ***
All Tests
    Wrapper    test_case_1


*** Keywords ***
Wrapper
    [Arguments]    ${case}
    Log    Generated case for ${case.operation.label}
