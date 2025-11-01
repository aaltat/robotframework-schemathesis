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

from DataDriver.AbstractReaderClass import AbstractReaderClass  # type: ignore
from DataDriver.ReaderConfig import TestCaseData  # type: ignore
from hypothesis import HealthCheck, Phase, Verbosity, given, settings
from hypothesis import strategies as st
from robot.api import logger
from robot.utils.importer import Importer  # type: ignore
from schemathesis import Case, openapi
from schemathesis.core.result import Ok


@dataclass
class Options:
    max_examples: int
    headers: dict[str, Any] | None = None
    path: "Path|None" = None
    url: str | None = None
    auth: str | None = None


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
        if self.options.auth:
            import_extensions(self.options.auth)
            logger.info(f"Using auth extension from: {self.options.auth}")

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


def import_extensions(library: str | Path) -> Any:
    """Import any extensions for SchemathesisLibrary."""
    importer = Importer("test library")
    lib = importer.import_module(library)
    logger.info(f"Imported extension module: {lib}")
    return lib
