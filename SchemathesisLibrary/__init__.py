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
from typing import Any

import schemathesis
from DataDriver import DataDriver  # type: ignore
from DataDriver.AbstractReaderClass import AbstractReaderClass  # type: ignore
from DataDriver.ReaderConfig import TestCaseData  # type: ignore
from hypothesis import HealthCheck, Phase, Verbosity, given, settings
from hypothesis import strategies as st
from robot.api.deco import keyword
from robot.result.model import TestCase as ResultTestCase  # type: ignore
from robot.result.model import TestSuite as ResultTestSuite  # type: ignore
from robot.running.model import TestCase, TestSuite  # type: ignore
from robotlibcore import DynamicCore  # type: ignore
from schemathesis.core.result import Ok  # type: ignore
from schemathesis.core.transport import Response

__version__ = "0.1.0"


@dataclass
class Options:
    url: "str|None" = None
    max_examples: int = 5


class SchemathesisReader(AbstractReaderClass):
    options: "Options|None" = None

    def get_data_from_source(self) -> list[TestCaseData]:
        # NOTE: (dd): It would be nice to support other schema loaders too
        schema = schemathesis.openapi.from_url(self.options.url)  # type: ignore
        all_cases: list[TestCaseData] = []
        for op in schema.get_all_operations():
            if isinstance(op, Ok):
                # NOTE: (dd): `as_strategy` also accepts GenerationMode
                #             It could be used to produce positive / negative tests
                strategy = op.ok().as_strategy().map(from_case)  # type: ignore
                add_examples(strategy, all_cases, self.options.max_examples)  # type: ignore
        return all_cases


def from_case(case: schemathesis.Case) -> TestCaseData:
    return TestCaseData(
        # NOTE: (dd): Not sure if a random `id` is useful here
        test_case_name=f"{case.operation.label} - {case.id}",
        arguments={"${case}": case},
    )


class SchemathesisLibrary(DynamicCore):
    ROBOT_LIBRARY_VERSION = __version__
    ROBOT_LISTENER_API_VERSION = 3
    ROBOT_LIBRARY_SCOPE = "TEST SUITE"

    def __init__(self, *, url: "str|None" = None) -> None:
        self.ROBOT_LIBRARY_LISTENER = self
        SchemathesisReader.options = Options(url=url)
        self.data_driver = DataDriver(reader_class=SchemathesisReader)
        DynamicCore.__init__(self, [])

    def _start_suite(self, data: TestSuite, result: ResultTestSuite) -> None:
        self.data_driver._start_suite(data, result)

    def _start_test(self, data: TestCase, result: ResultTestCase) -> None:
        self.data_driver._start_test(data, result)

    @keyword
    def call_and_validate(self, case: schemathesis.Case) -> Response:
        """Validate a Schemathesis case."""
        return case.call_and_validate()


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
