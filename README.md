# Robot Framework SchemathesisLibrary
Robot Framework SchemathesisLibrary is a library build top of the
[Schemathesis](https://github.com/schemathesis/schemathesis).
Schemathesis automatically generates thousands of test cases from
your OpenAPI or GraphQL schema and finds edge cases that break your
API.

SchemathesisLibrary uses
[DataDriver](https://github.com/Snooz82/robotframework-datadriver)
to create test cases from the Schemathesis
[Case](https://schemathesis.readthedocs.io/en/stable/reference/python/#schemathesis.Case)
object.

# Installation
Install with [pip](https://pypi.org/project/pip/), [uv](https://docs.astral.sh/uv/)
or any package manager that supports PyPi

```bash
pip install robotframework-schemathesislibrary
```

# Keyword documentation
See
[keyword documentation](https://aaltat.github.io/robotframework-schemathesis/SchemathesisLibrary.html)
for more details. A link older keyword documentation can be found from
[versions page](https://aaltat.github.io/robotframework-schemathesis/versions/)

# Usage
Test are automatically generated based your API specification, SchemathesisLibrary uses
DataDriver internally, but you need to create template suite, so that DataDriver is able
to create needed test for your test suite.

SchemathesisLibrary must be imported by `url` or `path` argument, which tell where
the API specification can obtained. As like with Datadriver, there must be
[Test Template](https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-templates)
setting defined. The template keyword must take one argument, usually referred as
`${case}` and the template keyword must call `Call And Validate` keyword with the
`${case}` argument.

Example test suite:
```robotframework
*** Settings ***
Library             SchemathesisLibrary    url=http://127.0.0.1/openapi.json

Test Template       Wrapper


*** Test Cases ***
All Tests   # This test is deleted by DataDriver
    Wrapper    test_case_1


*** Keywords ***
Wrapper
    [Arguments]    ${case}
    Call And Validate    ${case}

```
