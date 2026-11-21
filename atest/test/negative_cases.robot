*** Settings ***
Resource          runner.resource

Suite Setup       Run Suite Without Generation Mode
Suite Teardown    Remove Directory    ${CONFIG_DIR}    recursive=True


*** Variables ***
${CONFIG_DIR}    ${OUTPUT_DIR}${/}negative_cases


*** Test Cases ***
Positive Cases Pass
    Check Test Passed    ${LIBRARY_OUTPUT_XML}    POST /accepts-invalid - positive

Accepted Negative Cases Fail The Test
    Check Test Failed
    ...    ${LIBRARY_OUTPUT_XML}
    ...    POST /accepts-invalid - negative
    ...    *Schema-violating request accepted*


*** Keywords ***
Run Suite Without Generation Mode
    Create File    ${CONFIG_DIR}${/}schemathesis.toml
    ...    [[operations]]\nexclude-path = "/accepts-invalid"\nenabled = false\n
    Run Suite    rc=${None}    cwd=${CONFIG_DIR}
