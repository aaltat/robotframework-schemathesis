*** Settings ***
Library         os_wrapper.py
Library         TestSuiteChecker.py
Variables       variables.py
Resource        libs.resource


*** Variables ***
${LIBRARY_OUTPUT_XML}       ${None}


*** Keywords ***
Run Suite
    [Arguments]    ${rc: int}=0
    ${library_suite} =    Get Suite Path    ${SUITE_SOURCE}
    ${library_output_dir} =    Get Suite Output Path    ${SUITE_SOURCE}    ${LIBRARY_OUTPUT_DIR_BASE}
    Log    ${LIBRARY_PYTHON_PATH}
    Log    ${library_output_dir}
    VAR    @{args} =
    ...    run
    ...    robot
    ...    --loglevel
    ...    DEBUG:INFO
    ...    --pythonpath
    ...    ${LIBRARY_PYTHON_PATH}
    ...    --outputdir
    ...    ${library_output_dir}
    ...    --log
    ...    None
    ...    --report
    ...    None
    ...    ${library_suite}
    ${result} =    Run Process    uv    @{args}    cwd=${LIBRARY_PYTHON_PATH}
    Log    ${result.stdout}
    Log    ${result.stderr}
    Should Be Equal As Integers    ${result.rc}    ${rc}
    VAR    @{rebot_args} =
    ...    uv
    ...    run
    ...    rebot
    ...    --log
    ...    ${LIBRARY_OUTPUT_DIR_BASE}/log.html
    ...    --report
    ...    ${LIBRARY_OUTPUT_DIR_BASE}/report.html
    ...    ${LIBRARY_OUTPUT_DIR_BASE}${/}**${/}*.xml
    ${result} =    Run Process    @{rebot_args}    cwd=${LIBRARY_PYTHON_PATH}
    Log    ${result.stdout}
    Log    ${result.stderr}
    Should Be True    ${result.rc < 251}
    VAR    ${LIBRARY_OUTPUT_XML} =    ${library_output_dir}/output.xml    scope=SUITE
