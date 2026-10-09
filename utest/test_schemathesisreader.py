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
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from schemathesis import GenerationMode

from src.SchemathesisLibrary.schemathesisreader import Options, SchemathesisReader

DEFAULT_MAX_EXAMPLES = 100


@pytest.fixture
def mock_reader_config() -> Mock:
    mock_config = Mock()
    mock_config.file = None
    mock_config.encoding = None
    mock_config.dialect = None
    mock_config.delimiter = None
    mock_config.quotechar = None
    mock_config.escapechar = None
    mock_config.doublequote = None
    mock_config.skipinitialspace = None
    mock_config.lineterminator = None
    mock_config.sheet_name = None
    mock_config.list_separator = ","
    mock_config.handle_template_tags = None
    mock_config.kwargs = {}
    return mock_config


CONFIGURED_SCHEMA = """{
  "openapi": "3.0.0",
  "info": {"title": "Configured API", "version": "1.0.0"},
  "paths": {"/items": {"get": {
    "parameters": [{"name": "id", "in": "query", "required": true, "schema": {"type": "integer"}}],
    "responses": {"200": {"description": "ok"}}
  }}}
}"""


@pytest.fixture
def configured_schema(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    schema = tmp_path / "configured.json"
    schema.write_text(CONFIGURED_SCHEMA)
    return schema


def generate_modes(mock_reader_config: Mock, schema: Path, max_examples: int = 50) -> list[GenerationMode]:
    reader = SchemathesisReader(mock_reader_config)
    reader.options = Options(max_examples=max_examples, path=schema)
    return [case.arguments["${case}"]._meta.generation.mode for case in reader.get_data_from_source()]


NAMED_PROJECT = '[[project]]\ntitle = "Configured API"\n\n[project.generation]\n'


@pytest.mark.parametrize(
    ("config", "max_examples", "expected"),
    [
        (None, 5, 5),
        ("generation.max-examples = 3\n", DEFAULT_MAX_EXAMPLES, 3),
        (NAMED_PROJECT + "max-examples = 3\n", DEFAULT_MAX_EXAMPLES, 3),
    ],
    ids=["library-argument", "config", "named-project"],
)
def test_max_examples(
    mock_reader_config: Mock, configured_schema: Path, config: str | None, max_examples: int, expected: int
) -> None:
    if config is not None:
        (configured_schema.parent / "schemathesis.toml").write_text(config)

    assert len(generate_modes(mock_reader_config, configured_schema, max_examples)) == expected


@pytest.mark.parametrize(
    ("config", "expected"),
    [
        (None, set(GenerationMode)),
        ('generation.mode = "all"\n', set(GenerationMode)),
        ('generation.mode = "positive"\n', {GenerationMode.POSITIVE}),
        (NAMED_PROJECT + 'mode = "negative"\n', {GenerationMode.NEGATIVE}),
    ],
    ids=["default", "all", "positive", "named-project"],
)
def test_generation_mode(
    mock_reader_config: Mock, configured_schema: Path, config: str | None, expected: set[GenerationMode]
) -> None:
    if config is not None:
        (configured_schema.parent / "schemathesis.toml").write_text(config)

    assert set(generate_modes(mock_reader_config, configured_schema)) == expected


def test_operation_without_parameters_gets_its_only_case_once(
    mock_reader_config: Mock, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    schema = tmp_path / "good.json"
    schema.write_text(GOOD_SCHEMA)

    assert generate_modes(mock_reader_config, schema, 10) == [GenerationMode.POSITIVE]


def test_get_data_from_source_raises_value_error_when_options_not_set(mock_reader_config: Mock) -> None:
    reader = SchemathesisReader(mock_reader_config)
    reader.options = None
    with pytest.raises(ValueError, match="Options must be set before calling get_data_from_source"):
        reader.get_data_from_source()


def test_get_data_from_source_raises_value_error_for_invalid_path(mock_reader_config: Mock) -> None:
    reader = SchemathesisReader(mock_reader_config)
    invalid_path = Path("/nonexistent/file.yaml")
    reader.options = Options(max_examples=DEFAULT_MAX_EXAMPLES, path=invalid_path)

    with pytest.raises(ValueError, match="Provided path .* is not a valid file"):
        reader.get_data_from_source()


def test_get_data_from_source_raises_value_error_when_no_path_or_url(mock_reader_config: Mock) -> None:
    reader = SchemathesisReader(mock_reader_config)
    reader.options = Options(max_examples=DEFAULT_MAX_EXAMPLES)

    with (
        patch("src.SchemathesisLibrary.schemathesisreader.SchemathesisConfig.discover"),
        pytest.raises(ValueError, match="Either 'url' or 'path' must be provided"),
    ):
        reader.get_data_from_source()


BROKEN_SCHEMA = """{
  "openapi": "3.0.0",
  "info": {"title": "Broken", "version": "1.0.0"},
  "paths": {
    "/good": {"get": {"responses": {"200": {"description": "ok"}}}},
    "/bad": {"get": {"parameters": [{"$ref": "#/components/parameters/DoesNotExist"}],
             "responses": {"200": {"description": "ok"}}}}
  }
}"""


@pytest.fixture
def broken_schema(tmp_path: Path) -> Path:
    schema = tmp_path / "broken.json"
    schema.write_text(BROKEN_SCHEMA)
    return schema


def test_strict_raises_when_an_operation_can_not_be_parsed(
    mock_reader_config: Mock, broken_schema: Path
) -> None:
    reader = SchemathesisReader(mock_reader_config)
    reader.options = Options(max_examples=1, path=broken_schema, strict=True)

    with pytest.raises(ValueError, match=r"GET /bad"):
        reader.get_data_from_source()


def test_strict_is_the_default(mock_reader_config: Mock, broken_schema: Path) -> None:
    reader = SchemathesisReader(mock_reader_config)
    reader.options = Options(max_examples=1, path=broken_schema)

    with pytest.raises(ValueError, match=r"Failed to parse these parts of the schema"):
        reader.get_data_from_source()


def test_not_strict_skips_operations_that_can_not_be_parsed(
    mock_reader_config: Mock, broken_schema: Path
) -> None:
    reader = SchemathesisReader(mock_reader_config)
    reader.options = Options(max_examples=1, path=broken_schema, strict=False)

    cases = reader.get_data_from_source()

    assert len(cases) == 1
    assert "GET /good" in cases[0].test_case_name


@patch("src.SchemathesisLibrary.schemathesisreader.logger")
def test_not_strict_warns_about_operations_that_can_not_be_parsed(
    mock_logger: Mock, mock_reader_config: Mock, broken_schema: Path
) -> None:
    reader = SchemathesisReader(mock_reader_config)
    reader.options = Options(max_examples=1, path=broken_schema, strict=False)

    reader.get_data_from_source()

    warning = mock_logger.warn.call_args.args[0]
    assert "GET /bad" in warning
    assert "Unresolvable reference" in warning


EMPTY_SCHEMA = """{
  "openapi": "3.0.0",
  "info": {"title": "Empty", "version": "1.0.0"},
  "paths": {}
}"""


@pytest.fixture
def empty_schema(tmp_path: Path) -> Path:
    schema = tmp_path / "empty.json"
    schema.write_text(EMPTY_SCHEMA)
    return schema


def test_raises_when_the_schema_has_no_operations(mock_reader_config: Mock, empty_schema: Path) -> None:
    reader = SchemathesisReader(mock_reader_config)
    reader.options = Options(max_examples=1, path=empty_schema)

    with pytest.raises(ValueError, match="schema contains no operations"):
        reader.get_data_from_source()


def test_raises_when_no_operation_could_be_parsed(mock_reader_config: Mock, tmp_path: Path) -> None:
    """Not being strict must not turn a completely unusable schema into a passing run."""
    schema = tmp_path / "all_broken.json"
    schema.write_text(
        BROKEN_SCHEMA.replace('"/good": {"get": {"responses": {"200": {"description": "ok"}}}},', "")
    )
    reader = SchemathesisReader(mock_reader_config)
    reader.options = Options(max_examples=1, path=schema, strict=False)

    with pytest.raises(ValueError, match="no part of the schema could be parsed"):
        reader.get_data_from_source()


GOOD_SCHEMA = """{
  "openapi": "3.0.0",
  "info": {"title": "Good", "version": "1.0.0"},
  "paths": {"/good": {"get": {"responses": {"200": {"description": "ok"}}}}}
}"""


def test_base_url_tells_where_cases_of_a_file_loaded_schema_are_sent(
    mock_reader_config: Mock, tmp_path: Path
) -> None:
    schema = tmp_path / "good.json"
    schema.write_text(GOOD_SCHEMA)
    reader = SchemathesisReader(mock_reader_config)
    reader.options = Options(max_examples=1, path=schema, base_url="http://127.0.0.1:8000/api")

    case = reader.get_data_from_source()[0].arguments["${case}"]

    assert "http://127.0.0.1:8000/api/good" in case.as_curl_command()
