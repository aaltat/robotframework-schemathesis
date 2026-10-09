*** Settings ***
Resource       runner.resource

Suite Setup    Run Suite


*** Test Cases ***
Check Only Operations Left By Load Schema Hook Are Tested
    VAR    &{tests} =    DELETE=1
    Check Test Names And Counts    ${LIBRARY_OUTPUT_XML}    1    5    ${tests}
