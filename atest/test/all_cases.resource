*** Settings ***
Resource    libs.resource


*** Keywords ***
Get All Cases Test Description
    [Arguments]    ${count: int}=${5}
    VAR    @{test_description}

    VAR    @{logs}
    ...    Case: / | GET | {}
    ...    Case headers {} body 'Not set' cookies {} path parameters {}
    ...    Response: {'date': *, 'server': *, 'content-length': *, 'content-type': ?'application/json'?} | 200 | {"message":"Hello World","version":"1.0.0"}
    ...    Request: GET http://127.0.0.1/ headers: {'User-Agent': 'schemathesis*', 'Accept-Encoding': 'gzip, deflate', 'Accept': '*', 'Connection': 'keep-alive', 'X-Schemathesis-TestCaseId': '*'} body: None
    VAR    &{test}    name=GET / -    count=${1}    kw_logs_to_collect=Call And Validate    logs=${logs}
    Append To List    ${test_description}    ${test}

    VAR    @{logs}
    ...    Case: /items/{item_id} | GET | {'item_id': *}
    ...    Case headers {} body 'Not set' cookies {} path parameters {'item_id': *}
    ...    Response: {'date': *, 'server': *, 'content-length': *, 'content-type': *} | 200 | {"item_id":*,"q":*}
    ...    Request: GET http://127.0.0.1/items/* headers: {'User-Agent': 'schemathesis*', 'Accept-Encoding': 'gzip, deflate', 'Accept': '*', 'Connection': 'keep-alive', 'X-Schemathesis-TestCaseId': '*'} body: None
    VAR    &{test}
    ...    name=GET /items/{item_id}
    ...    count=${COUNT}
    ...    kw_logs_to_collect=Call And Validate
    ...    logs=${logs}
    Append To List    ${test_description}    ${test}

    VAR    @{logs}
    ...    Case: /items/{item_id} | PUT | {'item_id': *}
    ...    Case headers {} body {'name': *, 'price': *} cookies {} path parameters {'item_id': *}
    ...    Response: {'date': *, 'server': *, 'content-length': *, 'content-type': *} | 200 | {"item_name":*,"item_id":*,"price":*}
    ...    Request: PUT http://127.0.0.1/items/* headers: {'User-Agent': 'schemathesis*', 'Accept-Encoding': 'gzip, deflate', 'Accept': '*', 'Connection': 'keep-alive', 'X-Schemathesis-TestCaseId': '*', 'Content-Type': 'application/json', 'Content-Length': '*'} body: b'{"name": *, "price": *}'
    VAR    &{test}
    ...    name=PUT /items/{item_id}
    ...    count=${COUNT}
    ...    kw_logs_to_collect=Call And Validate
    ...    logs=${logs}
    Append To List    ${test_description}    ${test}

    VAR    @{logs}
    ...    Case: /items/{item_id} | DELETE | {'item_id': *}
    ...    Case headers {} body 'Not set' cookies {} path parameters {'item_id': *}
    ...    Response: {'date': *, 'server': *, 'content-length': *, 'content-type': ?'application/json'?} | 200 | {"message":"Item * deleted successfully"}
    ...    Request: DELETE http://127.0.0.1/items/* headers: {'User-Agent': 'schemathesis*', 'Accept-Encoding': 'gzip, deflate', 'Accept': '*', 'Connection': 'keep-alive', 'X-Schemathesis-TestCaseId': '*', 'Content-Length': '*'} body: None
    VAR    &{test}
    ...    name=DELETE /items/{item_id}
    ...    count=${COUNT}
    ...    kw_logs_to_collect=Call And Validate
    ...    logs=${logs}
    Append To List    ${test_description}    ${test}

    VAR    @{logs}
    ...    Case: /user/{userid} | GET | {'userid': *}
    ...    Case headers {'Authorization': 'Basic *'* body 'Not set' cookies {} path parameters {'userid': *}
    ...    Response: {'date': *, 'server': *, 'content-length': *, 'content-type': *'application/json'*} | 200 | {"username":"joulu","full_name":"Joulu Pukki","email":"joulu.pukki@korvatuntiri.fi","user_id":*}
    ...    Request: GET http://127.0.0.1/user/* headers: {'User-Agent': 'schemathesis*', 'Accept-Encoding': 'gzip, deflate', 'Accept': '*', 'Connection': *, 'Authorization': 'Basic am91bHU6cHVra2k=', 'X-Schemathesis-TestCaseId': '*'} body: None
    VAR    &{test}
    ...    name=GET /user/{userid} -
    ...    count=${COUNT}
    ...    kw_logs_to_collect=Call And Validate
    ...    logs=${logs}
    Append To List    ${test_description}    ${test}
    RETURN    ${test_description}

Get All Cases Test Description Separate
    [Arguments]    ${count: int}=${5}
    ${test_description} =    Get All Cases Test Description    ${COUNT}
    FOR    ${description}    IN    @{test_description}
        Append To List    ${description}[logs]    Response validation passed.
        Append To List
        ...    ${description}[logs]
        ...    Validating response: 200 | {'date': *, 'server': *, 'content-length': *, 'content-type': *'application/json'*}
    END
    RETURN    ${test_description}
