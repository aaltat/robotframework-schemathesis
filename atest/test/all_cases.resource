*** Keywords ***
Get All Cases Test Description
    [Arguments]    ${count: int}=${5}
    VAR    @{test_description}

    VAR    @{logs}
    ...    Case: / | GET | {}
    ...    Case headers {} body 'Not set' cookies {} path parameters {}
    ...    Response: {'date': *, 'server': *, 'content-length': *, 'content-type': ?'application/json'?} | 200 | {"message":"Hello World","version":"1.0.0"}
    VAR    &{logs_description}    logs=${logs}
    VAR    &{test}    name=GET / -    count=${1}    kw_logs_to_collect=Call And Validate    logs=${logs_description}
    Append To List    ${test_description}    ${test}

    VAR    @{logs}
    ...    Case: /items/{item_id} | GET | {'item_id': *}
    ...    Case headers {} body 'Not set' cookies {} path parameters {'item_id': *}
    ...    Response: {'date': *, 'server': *, 'content-length': *, 'content-type': *} | 200 | {"item_id":*,"q":*}
    VAR    &{logs_description}    logs=${logs}
    VAR    &{test}
    ...    name=GET /items/{item_id}
    ...    count=${COUNT}
    ...    kw_logs_to_collect=Call And Validate
    ...    logs=${logs_description}
    Append To List    ${test_description}    ${test}

    VAR    @{logs}
    ...    Case: /items/{item_id} | PUT | {'item_id': *}
    ...    Case headers {} body {'name': *, 'price': *} cookies {} path parameters {'item_id': *}
    ...    Response: {'date': *, 'server': *, 'content-length': *, 'content-type': *} | 200 | {"item_name":*,"item_id":*,"price":*}
    VAR    &{logs_description}    logs=${logs}
    VAR    &{test}    name=PUT /items/{item_id}    count=${COUNT}    kw_logs_to_collect=Call And Validate    logs=${logs_description}
    Append To List    ${test_description}    ${test}

    VAR    @{logs}
    ...    Case: /items/{item_id} | DELETE | {'item_id': *}
    ...    Case headers {} body 'Not set' cookies {} path parameters {'item_id': *}
    ...    Response: {'date': *, 'server': *, 'content-length': *, 'content-type': ?'application/json'?} | 200 | {"message":"Item * deleted successfully"}
    VAR    &{logs_description}    logs=${logs}
    VAR    &{test}
    ...    name=DELETE /items/{item_id}
    ...    count=${COUNT}
    ...    kw_logs_to_collect=Call And Validate
    ...    logs=${logs_description}
    Append To List    ${test_description}    ${test}

    VAR    @{logs}
    ...    Case: /user/{userid} | GET | {'userid': *}
    ...    Case headers {'Authorization': 'Basic *'* body 'Not set' cookies {} path parameters {'userid': *}
    ...    Response: {'date': *, 'server': *, 'content-length': *, 'content-type': *'application/json'*} | 200 | {"username":"joulu","full_name":"Joulu Pukki","email":"joulu.pukki@korvatuntiri.fi","user_id":*}
    VAR    &{logs_description}    logs=${logs}
    VAR    &{test}
    ...    name=GET /user/{userid} -
    ...    count=${COUNT}
    ...    kw_logs_to_collect=Call And Validate
    ...    logs=${logs_description}
    Append To List    ${test_description}    ${test}
    RETURN    ${test_description}
