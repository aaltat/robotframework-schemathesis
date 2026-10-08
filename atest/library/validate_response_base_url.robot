*** Settings ***
Variables        authentication.py
Library          SchemathesisLibrary
...                  path=${CURDIR}/../specs/test-app/openapi.json
...                  max_examples=5
...                  base_url=http://127.0.0.1:1/

Test Template    Wrapper


*** Test Cases ***
All Tests
    Wrapper    test_case_1


*** Keywords ***
Wrapper
    [Arguments]    ${case}
    # Nothing listens on the library base URL, so validation passes only when the checks' extra requests
    # go to the server the response came from.
    ${r} =    Call    ${case}    base_url=http://127.0.0.1/    auth=${BASIC_AUTH_TUPLE}
    Validate Response    ${case}    ${r}    auth=${BASIC_AUTH_TUPLE}
