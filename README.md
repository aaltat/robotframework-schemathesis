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

# Authentication

## Dynamic token authentication
Library currently supports Schemathesis
[dynamic token](https://schemathesis.readthedocs.io/en/stable/guides/auth/#dynamic-token-authentication)
authentication by the library import `auth` argument. The dynamic token generation
class should follow the Schemathesis documentation. The only addition is the import.
Importing the class must follow the Robot Framework library
[import rules](https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#specifying-library-to-import)
, example if importing with filename, filename much match to the class name. Example
if test case looks like:

```robotframework
*** Settings ***
Library             SchemathesisLibrary    url=http://127.0.0.1/openapi.json    auth=${CURDIR}/AuthExtension.py
Test Template       Wrapper

*** Test Cases ***
All Tests
    Wrapper    test_case_1

*** Keywords ***
Wrapper
    [Arguments]    ${case}
    Call And Validate    ${case}
```
And `AuthExtension.py` looks like
```python
from base64 import b64encode

import schemathesis
from robot.api import logger


@schemathesis.auth()
class AuthExtension:
    def get(self, case, ctx):
        # Instead of hard coding secrets to class, it is better to get them dynamically.
        # Jenkins or GitHub secrets, Azure keyvault, or from somewhere which is appropriate
        # for your needs.
        return b64encode("joulu:pukki".encode("utf-8")).decode("ascii")

    def set(self, case, data, ctx):
        case.headers = case.headers or {}
        case.headers["Authorization"] = f"Basic {data}"
        logger.debug(f"Updated headers for case: {case.operation.method} {case.operation.path}")
```
Then with all API calls, will have
[basic auth](https://en.wikipedia.org/wiki/Basic_access_authentication) set in the
headers for all calls made to your API endpoint.
