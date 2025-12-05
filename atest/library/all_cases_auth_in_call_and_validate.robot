*** Settings ***
Library             SchemathesisLibrary    url=http://127.0.0.1/openapi.json
Variables           authentication.py

Test Template       Wrapper


*** Test Cases ***
All Tests
    Wrapper    test_case_1


*** Keywords ***
Wrapper
    [Arguments]    ${case}
    IF    ${{'${case.path}'.startswith('/user')}}
        VAR    &{headers} =    key1=value1    key2=value2
    ELSE
        VAR    &{headers} =
    END
    ${r} =    Call And Validate    ${case}    auth=${BASIC_AUTH_TUPLE}
    Log    ${r.json()}
