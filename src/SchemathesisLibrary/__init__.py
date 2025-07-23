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
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from DataDriver import DataDriver  # type: ignore
from DataDriver.AbstractReaderClass import AbstractReaderClass  # type: ignore
from DataDriver.ReaderConfig import TestCaseData  # type: ignore
from hypothesis import HealthCheck, Phase, Verbosity, given, settings
from hypothesis import strategies as st
from robot.api import logger
from robot.api.deco import keyword
from robot.result.model import TestCase as ResultTestCase  # type: ignore
from robot.result.model import TestSuite as ResultTestSuite  # type: ignore
from robot.running.model import TestCase, TestSuite  # type: ignore
from robotlibcore import DynamicCore  # type: ignore
from schemathesis import Case, openapi
from schemathesis.core import NotSet
from schemathesis.core.result import Ok
from schemathesis.core.transport import Response

__version__ = "0.15.0"


@dataclass
class Options:
    max_examples: int
    headers: dict[str, Any] | None = None
    path: "Path|None" = None
    url: "str|None" = None


class SchemathesisReader(AbstractReaderClass):
    options: "Options|None" = None

    def get_data_from_source(self) -> list[TestCaseData]:
        if not self.options:
            raise ValueError("Options must be set before calling get_data_from_source.")
        url = self.options.url
        path = self.options.path
        if path and not Path(path).is_file():
            raise ValueError(f"Provided path '{path}' is not a valid file.")
        if path:
            schema = openapi.from_path(path)
        elif url:
            headers = self.options.headers or {}
            schema = openapi.from_url(url, headers=headers)
        else:
            raise ValueError("Either 'url' or 'path' must be provided to SchemathesisLibrary.")
        all_cases: list[TestCaseData] = []
        for op in schema.get_all_operations():
            if isinstance(op, Ok):
                # NOTE: (dd): `as_strategy` also accepts GenerationMode
                #             It could be used to produce positive / negative tests
                strategy = op.ok().as_strategy().map(from_case)  # type: ignore
                add_examples(strategy, all_cases, self.options.max_examples)  # type: ignore
        return all_cases


def from_case(case: Case) -> TestCaseData:
    return TestCaseData(
        test_case_name=f"{case.operation.label} - {case.id}",
        arguments={"${case}": case},
    )


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
    ) -> None:
        """The SchemathesisLibrary can be initialized with the following arguments:

        | =Argument=                        | =Description= |
        | `headers`                         | Optional HTTP headers to be used schema is downloaded from `url`. |
        | `max_examples`                    | Maximum number of examples to generate for each operation. Default is 5. |
        | `path`                            | Path to the OpenAPI schema file. Using either `path` or `url` is mandatory. |
        | `url`                             | URL where the OpenAPI schema can be downloaded. |
        """
        self.ROBOT_LIBRARY_LISTENER = self
        SchemathesisReader.options = Options(headers=headers, max_examples=max_examples, path=path, url=url)
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
        auth: "Any|None" = None,
        base_url: "str|None" = None,
        headers: "dict[str, Any]|None" = None,
    ) -> Response:
        """Call and validate a Schemathesis case.

        Example:
        | ${response} =    Call And Validate Case    ${case}
        """
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
        auth: "Any|None" = None,
        base_url: "str|None" = None,
        headers: "dict[str, Any]|None" = None,
    ) -> Response:
        """Call a Schemathesis case without validation.

        The `Call` and `Validate Response` keywords can be used together
        to call a case and validate the response.

        Example:
        | ${response} =    Call Case    ${case}
        | Validate Response    ${case}    ${response}
        """
        self.info(f"Calling case: {case.path} | {case.method} | {case.path_parameters}")
        self._log_case(case)
        response = case.call(base_url=base_url, headers=headers, auth=auth)
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


def add_examples(strategy: st.SearchStrategy, container: list[TestCaseData], max_examples: int) -> None:
    @given(strategy)
    @settings(
        database=None,
        max_examples=max_examples,
        deadline=None,
        verbosity=Verbosity.quiet,
        phases=(Phase.generate,),
        suppress_health_check=list(HealthCheck),
    )
    def example_generating_inner_function(ex: Any) -> None:
        container.append(ex)

    example_generating_inner_function()
