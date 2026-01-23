*** Settings ***
Resource            runner.resource
Resource            all_cases.resource

Suite Setup         Set Configuration File And Run Suite
Suite Teardown      Remove Configuration File


*** Test Cases ***
Check All Cases
    Check Specific Test Logs
    ...    ${LIBRARY_OUTPUT_XML}
    ...    Case headers
    ...    number_of_tests=9
    ...    string_in_log=path parameters


*** Keywords ***
Set Configuration File And Run Suite
    Log    Create ${EXECDIR}/schemathesis.toml
    Create File    ${EXECDIR}/schemathesis.toml
    ...    generation.max-examples = 2
    Run Suite

Remove Configuration File
    Remove File    ${EXECDIR}/schemathesis.toml
