*** Settings ***
Variables        authentication.py
Library          SchemathesisLibrary
...                  url=https://127.0.0.1:8443/openapi.json
...                  max_examples=5
...                  tls_verify=False

Test Template    Wrapper


*** Test Cases ***
All Tests
    Wrapper    test_case_1


*** Keywords ***
Wrapper
    [Arguments]    ${case}
    # The test app answers on port 8443 with a self-signed certificate, so both the schema download
    # and the calls pass only when TLS verification is turned off.
    ${r} =    Call And Validate    ${case}    auth=${BASIC_AUTH_TUPLE}
    Log    ${r.json()}
