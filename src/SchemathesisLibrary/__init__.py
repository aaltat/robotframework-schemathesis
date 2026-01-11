# Copyright 2025-     Tatu Aalto
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import TYPE_CHECKING, Any

from DataDriver import DataDriver  # type: ignore
from robot.api import logger
from robot.api.deco import keyword
from robot.result.model import TestCase as ResultTestCase  # type: ignore
from robot.result.model import TestSuite as ResultTestSuite  # type: ignore
from robot.running.model import TestCase, TestSuite  # type: ignore
from robot.utils.dotdict import DotDict  # type: ignore
from robotlibcore import DynamicCore  # type: ignore
from schemathesis import Case
from schemathesis.core import NotSet
from schemathesis.core.transport import Response

from .schemathesisreader import Options, SchemathesisReader

if TYPE_CHECKING:
    from pathlib import Path

__version__ = "2.0.0"


class SchemathesisLibrary(DynamicCore):
    """SchemathesisLibrary is a library for validating API schema using Schemathesis.

    %TOC%

    Example usage of the library and the `Call And Validate` keyword

    Library must be imported with the ``url`` or ``path`` argument to specify the
    OpenAPI schema. The library uses
    [https://github.com/Snooz82/robotframework-datadriver|DataDriver] to generate
    test cases from the OpenAPI schema by using
    [https://github.com/schemathesis/schemathesis|Schemathesis]. The library
    creates test cases that takes one argument, ``${case}``, which is a
    Schemathesis
    [https://schemathesis.readthedocs.io/en/stable/reference/python/#schemathesis.Case|Case]
    object. The `Call And Validate` keyword can be used to call and validate
    the case. The keyword will log the request and response details.

    Example:
    | *** Settings ***
    | Library             SchemathesisLibrary    url=http://127.0.0.1/openapi.json
    |
    | Test Template       Wrapper
    |
    | *** Test Cases ***
    | All Tests   # This test is deleted by DataDriver
    |     Wrapper    test_case_1
    |
    | *** Keywords ***
    | Wrapper
    |     [Arguments]    ${case}
    |     Call And Validate    ${case}
    """

    ROBOT_LIBRARY_VERSION = __version__
    ROBOT_LISTENER_API_VERSION = 3
    ROBOT_LIBRARY_SCOPE = "TEST SUITE"

    def __init__(  # noqa: PLR0913
        self,
        *,
        headers: "dict[str, Any]|None" = None,
        max_examples: int = 100,
        path: "Path|None" = None,
        url: "str|None" = None,
        auth: str | None = None,
        hook: str | None = None,
    ) -> None:
        """The SchemathesisLibrary can be initialized with the following arguments:

        | =Argument= | =Description= |
        | ``headers`` | Optional HTTP headers to be used when schema is downloaded from ``url``. |
        | ``max_examples`` | Maximum number of examples to generate for each operation. Default is 5. |
        | ``path`` | Path to the OpenAPI schema file. Using either ``path`` or ``url`` is mandatory. |
        | ``url`` | URL where the OpenAPI schema can be downloaded. |
        | ``auth`` | Optional authentication class to be used passed for Schemathesis authentication when test cases are executed. |
        | ``hook`` | Optional Schemathesis hook https://schemathesis.readthedocs.io/en/stable/guides/extending/. |

        The ``headers`` argument is only needed when the schema is downloaded from a URL and there is need to pass example
        authentication headers to the endpoint. The ``headers`` is not used in the API calls are made during test execution.

        ``path`` and ``url`` are mutually exclusive, only one of them should be used to specify the OpenAPI schema location.

        ``auth`` can be used create Schemathesis
        [https://schemathesis.readthedocs.io/en/stable/guides/auth/#dynamic-token-authentication|dynamic token]
        authentication for the test cases. The dynamic token generation class should
        follow the Schemathesis documentation. The only addition is the import and importing
        the class must follow the Robot Framework library
        [https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#specifying-library-to-import|import rules]
        . Example if importing with filename, filename much match to the class name.
        See example from
        [https://github.com/aaltat/robotframework-schemathesis?tab=readme-ov-file##dynamic-token-authentication|README.md]
        file

        The ``hook`` argument can be used to specify Schemathesis hooks to modify the generated test cases. The hooks
        implementation must follow the Schemathesis documentation:
        https://schemathesis.readthedocs.io/en/stable/guides/extending/ Hooks importing follows same rules as importing
        [https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#specifying-library-to-import|test libraries]
        in Robot Framework. Multiple hooks can be specified by separating them with semicolon (;).
        """
        self.ROBOT_LIBRARY_LISTENER = self
        SchemathesisReader.options = Options(
            headers=headers,
            max_examples=max_examples,
            path=path,
            url=url,
            auth=auth,
            hook=hook,
        )
        self.data_driver = DataDriver(reader_class=SchemathesisReader)
        DynamicCore.__init__(self, [])

    def _start_suite(self, data: TestSuite, result: ResultTestSuite) -> None:
        self.data_driver._start_suite(data, result)

    def _start_test(self, data: TestCase, result: ResultTestCase) -> None:
        self.data_driver._start_test(data, result)

    @keyword
    def call_and_validate(
        self,
        case: Case,
        *,
        base_url: str | None = None,
        headers: dict[str, Any] | None = None,
        auth: tuple[str, str] | Any | None = None,
    ) -> Response:
        """Call and validate a Schemathesis case.

        | Argument   | Description |
        | ``case``     | The Schemathesis [https://schemathesis.readthedocs.io/en/stable/reference/python/#schemathesis.Case|Case] to be called and validated. |
        | ``base_url`` | Optional base URL to override the one defined in the schema. Need mostly when schema is read from a file. |
        | ``headers``  | Optional HTTP headers to be added when calling the API endpoint. |
        | ``auth``     | Optional authentication to be used when calling the case. |

        ``auth`` can be any authentication supported by
        [https://www.python-httpx.org/advanced/authentication/|httpx authentication].
        Example a tuple containing username and password for basic authentication or
        and instance of
        [https://www.python-httpx.org/advanced/authentication/#digest-authentication|Digest authentication]

        Returns a
        [https://schemathesis.readthedocs.io/en/stable/reference/python/#schemathesis.Response|Schemathesis Response]
        object. Can be used to further validate the response, example check specific headers
        or response body.

        Example:
        | ${response} =    `Call And Validate`    ${case}
        | VAR     ${body}    ${response.json()}
        | Should Be True    ${body}    # Or whatever validation is needed by users
        """
        logger.info(f"auth: {auth} {type(auth)}")
        headers = self._dot_dict_to_dict(headers) if headers else None
        self.info(f"Case: {case.path} | {case.method} | {case.path_parameters}")
        self._log_case(case, headers)
        response = case.call_and_validate(base_url=base_url, headers=headers, auth=auth)
        self._log_request(response)
        self.debug(f"Response: {response.headers} | {response.status_code} | {response.text}")
        return response

    @keyword
    def call(
        self,
        case: Case,
        *,
        base_url: str | None = None,
        headers: dict[str, Any] | None = None,
        auth: tuple[str, str] | Any | None = None,
    ) -> Response:
        """Call a Schemathesis case without validation.

        | =Argument=   | =Description= |
        | ``case``     | The Schemathesis [https://schemathesis.readthedocs.io/en/stable/reference/python/#schemathesis.Case|Case] to be called and validated. |
        | ``base_url`` | Optional base URL to override the one defined in the schema. Need mostly when schema is read from a file. |
        | ``headers``  | Optional HTTP headers to be added when calling the API endpoint. |
        | ``auth``     | Optional authentication to be used when calling the case. |

        ``auth`` can be any authentication supported by
        [https://www.python-httpx.org/advanced/authentication/|httpx authentication].
        Example a tuple containing username and password for basic authentication or
        and instance of
        [https://www.python-httpx.org/advanced/authentication/#digest-authentication|Digest authentication]

        Returns a
        [https://schemathesis.readthedocs.io/en/stable/reference/python/#schemathesis.Response|Schemathesis Response]
        object. Can be used to further validate the response, example check specific headers
        or response body.

        The `Call` and `Validate Response` keywords can be used together
        to call a case and validate the response.

        Example:
        | ${response} =    `Call`    ${case}
        | `Validate Response`    ${case}    ${response}

        """
        headers = self._dot_dict_to_dict(headers) if headers else None
        self.info(f"Calling case: {case.path} | {case.method} | {case.path_parameters}")
        self._log_case(case)
        response = case.call(base_url=base_url, headers=headers, auth=auth)
        self._log_request(response)
        return response

    @keyword
    def validate_response(
        self,
        case: Case,
        response: Response,
        headers: dict[str, Any] | None = None,
        auth: tuple[str, str] | Any | None = None,
    ) -> None:
        """Validate a Schemathesis response.

        | Argument   | Description |
        | ``case``     | The Schemathesis case to be validated against. |
        | ``response`` | The Schemathesis response to be validated. Returned by ``Call`` keyword. |
        | ``headers``  | Optional HTTP headers to be added when calling the API endpoint. |
        | ``auth``     | Optional authentication to be used when calling the case. |

        ``auth`` can be any authentication supported by
        [https://www.python-httpx.org/advanced/authentication/|httpx authentication].
        Example a tuple containing username and password for basic authentication or
        and instance of
        [https://www.python-httpx.org/advanced/authentication/#digest-authentication|Digest authentication]

        The response is validated against the case's expectations.
        The `Call` and `Validate Response` keywords can be used together
        to call a case and validate the response. See the example from
        `Call` keyword documentation.
        """
        self.info(f"Validating response: {response.status_code} | {response.headers}")
        transport_kwargs: dict[str, Any] = {}
        if auth:
            transport_kwargs["auth"] = auth
        if headers:
            transport_kwargs["headers"] = headers
        case.validate_response(response=response, transport_kwargs=transport_kwargs)
        self.info("Response validation passed.")

    def info(self, message: str) -> None:
        logger.info(message)

    def debug(self, message: str) -> None:
        logger.debug(message)

    def _log_case(
        self,
        case: Case,
        headers: "dict[str, Any]|None" = None,
    ) -> None:
        body = case.body if not isinstance(case.body, NotSet) else "Not set"
        case_headers = headers if headers else case.headers
        self.debug(
            f"Case headers {case_headers!r} body {body!r} "
            f"cookies {case.cookies!r} path parameters {case.path_parameters!r}"
        )

    def _log_request(self, resposen: Response) -> None:
        self.debug(
            f"Request: {resposen.request.method} {resposen.request.url} "
            f"headers: {resposen.request.headers!r} body: {resposen.request.body!r}"
        )

    def _dot_dict_to_dict(self, dot_dict: dict[str, Any]) -> dict[str, Any]:
        if isinstance(dot_dict, DotDict):
            return dict(dot_dict)
        return dot_dict
