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

__version__ = "0.1.0"


@dataclass
class Options:
    url: "str|None" = None


class SchemathesisReader(AbstractReaderClass):
    options: "Options|None" = None

    def get_data_from_source(
        self,
    ) -> list[TestCaseData]:
        schema = schemathesis.from_uri(self.options.url)  # type: ignore
        all_cases = []
        for op in schema.get_all_operations():
            op_as_strategy = op.ok().as_strategy()  # type: ignore
            for case in generate_examples(op_as_strategy, 5):
                args = {
                    "${case}": case,
                }
                path_params = case.path_parameters if case.path_parameters else ""
                all_cases.append(
                    TestCaseData(
                        test_case_name=f"{case.method} {case.full_path} {path_params}", arguments=args
                    )
                )
        return all_cases


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
    def call_and_validate(self, case: schemathesis.Case) -> None:
        """Validate a Schemathesis case."""
        case.call_and_validate()


def generate_examples(strategy: st.SearchStrategy, number: int) -> list[schemathesis.Case]:
    examples = []

    @given(strategy)
    @settings(
        database=None,
        max_examples=number,
        deadline=None,
        verbosity=Verbosity.quiet,
        phases=(Phase.generate,),
        suppress_health_check=list(HealthCheck),
    )
    def example_generating_inner_function(ex: Any) -> None:
        examples.append(ex)

    example_generating_inner_function()
    return examples
