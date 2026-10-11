*** Settings ***
Resource       runner.resource

Suite Setup    Run Suite    ${1}


*** Test Cases ***
Check Failure
    # The test app certificate is self-signed, so the schema download fails when TLS verification is on.
    VAR    @{logs} =    *LoaderError: SSL verification problem*
    Check Suite With Logs    ${LIBRARY_OUTPUT_XML}    ${logs}
