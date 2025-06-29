*** Settings ***
Variables           authentication.py
Library             SchemathesisLibrary    url=http://127.0.0.1/openapi.json

Test Template       Wrapper


*** Test Cases ***
All Tests
    Wrapper    test_case_1


*** Keywords ***
Wrapper
    [Arguments]    ${case}
    IF    ${{'${case.path}'.startswith('/user')}}
        VAR    ${auth}    ${BASIC_AUTH_TUPLE}
    ELSE
        VAR    ${auth}    ${None}
    END
    ${r} =    Call And Validate    ${case}    auth=${auth}
    Log    ${r.json()}
