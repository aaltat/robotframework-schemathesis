*** Settings ***
Library         Process
Library         os_wrapper.py
Library         TestSuiteChecker.py
Variables       variables.py


*** Variables ***
${LIBRARY_OUTPUT_XML}       ${None}


*** Keywords ***
Run Suite
    ${library_suite} =    Get Suite Path    ${SUITE_SOURCE}
    Log    ${LIBRARY_PYTHON_PATH}
    Log    ${LIBRARY_OUTPUT_DIR}
    VAR    @{args}
    ...    run
    ...    robot
    ...    --loglevel
    ...    DEBUG:INFO
    ...    --pythonpath
    ...    ${LIBRARY_PYTHON_PATH}
    ...    --outputdir
    ...    ${LIBRARY_OUTPUT_DIR}
    ...    ${library_suite}
    ${result} =    Run Process    uv    @{args}    cwd=${LIBRARY_PYTHON_PATH}
    Log    ${result.stdout}
    Log    ${result.stderr}
    Should Be Equal As Integers    ${result.rc}    0
    VAR    ${LIBRARY_OUTPUT_XML}    ${LIBRARY_OUTPUT_DIR}/output.xml    scope=SUITE
