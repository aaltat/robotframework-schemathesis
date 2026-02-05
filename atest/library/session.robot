*** Settings ***
Variables           authentication.py
Library             RequestsLibrary
Library             SchemathesisLibrary
...                     url=http://127.0.0.1/openapi.json
...                     max_examples=4
Library             ${CURDIR}/request_session.py

Test Template       Wrapper


*** Test Cases ***
All Tests
    Wrapper    test_case_1


*** Keywords ***
Wrapper
    [Arguments]    ${case}
    Create Session    session    http://127.0.0.1/
    ${session} =    Get Request Session
    ${r} =    Call And Validate    ${case}    headers=&{BASIC_AUTH_HEADERS}    session=${session}
    VAR    ${body} =    ${r.json()}
    Should Be True    ${body}
