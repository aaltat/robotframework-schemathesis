*** Settings ***
Resource        runner.resource
Resource        all_cases.resource

Suite Setup     Run Suite


*** Test Cases ***
Check All Cases
    VAR    &{tests} =    GET=11    PUT=1
    Check Test Names And Counts    ${LIBRARY_OUTPUT_XML}    17    18    ${tests}
