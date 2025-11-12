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

__version__ = "1.1.0"


class SchemathesisLibrary(DynamicCore):
    """SchemathesisLibrary is a library for validating API cases using Schemathesis.

    %TOC%

    Example usage of the library and the `Call And Validate` keyword

    Library must be imported with the `url` or `path` argument to specify the
    OpenAPI schema. The library uses
    [https://github.com/Snooz82/robotframework-datadriver|DataDriver] to generate
    test cases from the OpenAPI schema by using
    [https://github.com/schemathesis/schemathesis|Schemathesis]. The library
    creates test cases that takes one argument, `${case}`, which is a
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

    def __init__(
        self,
        *,
        headers: "dict[str, Any]|None" = None,
        max_examples: int = 5,
        path: "Path|None" = None,
        url: "str|None" = None,
        auth: str | None = None,
    ) -> None:
        """The SchemathesisLibrary can be initialized with the following arguments:

        | =Argument=                        | =Description= |
        | `headers`                         | Optional HTTP headers to be used when schema is downloaded from `url`. |
        | `max_examples`                    | Maximum number of examples to generate for each operation. Default is 5. |
        | `path`                            | Path to the OpenAPI schema file. Using either `path` or `url` is mandatory. |
        | `url`                             | URL where the OpenAPI schema can be downloaded. |
        | `auth`                            | Optional authentication class to be used passed for Schemathesis authentication when test cases are executed. |
        """
        self.ROBOT_LIBRARY_LISTENER = self
        SchemathesisReader.options = Options(
            headers=headers, max_examples=max_examples, path=path, url=url, auth=auth
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
    ) -> Response:
        """Call and validate a Schemathesis case.

        Example:
        | ${response} =    Call And Validate Case    ${case}
        """
        headers = self._dot_dict_to_dict(headers) if headers else None
        self.info(f"Case: {case.path} | {case.method} | {case.path_parameters}")
        self._log_case(case, headers)
        response = case.call_and_validate(base_url=base_url, headers=headers)
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
    ) -> Response:
        """Call a Schemathesis case without validation.

        The `Call` and `Validate Response` keywords can be used together
        to call a case and validate the response.

        Example:
        | ${response} =    Call Case    ${case}
        | Validate Response    ${case}    ${response}
        """
        headers = self._dot_dict_to_dict(headers) if headers else None
        self.info(f"Calling case: {case.path} | {case.method} | {case.path_parameters}")
        self._log_case(case)
        response = case.call(base_url=base_url, headers=headers)
        self._log_request(response)
        return response

    @keyword
    def validate_response(self, case: Case, response: Response) -> None:
        """Validate a Schemathesis response.

        The response is validated against the case's expectations.
        The `Call` and `Validate Response` keywords can be used together
        to call a case and validate the response. See the example from
        `Call` keyword documentation.
        """
        self.info(f"Validating response: {response.status_code} | {response.headers}")
        case.validate_response(response)
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
