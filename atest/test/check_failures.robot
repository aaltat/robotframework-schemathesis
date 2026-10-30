*** Settings ***
Resource       runner.resource

Suite Setup    Run Suite    ${5}


*** Test Cases ***
Server Error Fails The Test
    Check Test Failed    ${LIBRARY_OUTPUT_XML}    GET /server-error    *Server error*

Response Violating The Schema Fails The Test
    Check Test Failed    ${LIBRARY_OUTPUT_XML}    GET /schema-violation    *Response violates schema*

Wrong Content Type Fails The Test
    Check Test Failed    ${LIBRARY_OUTPUT_XML}    GET /wrong-content-type    *Undocumented Content-Type*

Undocumented Status Code Fails The Test
    Check Test Failed    ${LIBRARY_OUTPUT_XML}    GET /undocumented-status    *Undocumented HTTP status code*

Missing Response Header Fails The Test
    Check Test Failed    ${LIBRARY_OUTPUT_XML}    GET /missing-header    *Missing required headers*
