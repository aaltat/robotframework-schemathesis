*** Settings ***
Resource        runner.resource

Suite Setup     Run Suite


*** Test Cases ***
Check All Cases
    VAR    &{test_description}
    ...    DELETE /=${5}
    ...    PUT /=${5}
    ...    GET / =${1}
    ...    GET /items/{item_id}=${5}
    Check Suite    ${LIBRARY_OUTPUT_XML}    16    ${test_description}
