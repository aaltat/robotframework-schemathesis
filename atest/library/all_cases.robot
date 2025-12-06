*** Settings ***
Variables           authentication.py
Library             SchemathesisLibrary    url=http://127.0.0.1/openapi.json    max_examples=4    headers=${BASIC_AUTH_HEADERS}

Test Template       Wrapper


*** Test Cases ***
All Tests
    Wrapper    test_case_1


*** Keywords ***
Wrapper
    [Arguments]    ${case}
    IF    ${{'${case.path}'.startswith('/user')}}
        VAR    &{headers} =    &{BASIC_AUTH_HEADERS}
    ELSE
        VAR    &{headers} =
    END
    ${r} =    Call And Validate    ${case}    headers=${headers}
    VAR    ${body} =    ${r.json()}
    Should Be True    ${body}
