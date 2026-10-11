*** Settings ***
Resource          runner.resource
Resource          all_cases.resource

Suite Setup       Set Configuration File And Run Suite
Suite Teardown    Remove Directory    ${CONFIG_DIR}    recursive=True


*** Variables ***
${CONFIG_DIR}    ${OUTPUT_DIR}${/}config_file


*** Test Cases ***
Check All Cases
    Check Specific Test Logs
    ...    ${LIBRARY_OUTPUT_XML}
    ...    Case headers
    ...    number_of_tests=9
    ...    string_in_log=path parameters


*** Keywords ***
Set Configuration File And Run Suite
    Create File    ${CONFIG_DIR}${/}schemathesis.toml
    ...    [[project]]\ntitle = "Test API"\n\n[project.generation]\nmax-examples = 2\nmode = "positive"\n
    Run Suite    cwd=${CONFIG_DIR}
