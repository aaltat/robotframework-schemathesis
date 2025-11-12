*** Settings ***
Variables           authentication.py
Library             SchemathesisLibrary    path=${CURDIR}/../specs/openapi.json    auth=${CURDIR}/AuthExtension.py

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
    ${r} =    Call And Validate    ${case}    base_url=http://127.0.0.1/    headers=${headers}
    Log    ${r.json()}
