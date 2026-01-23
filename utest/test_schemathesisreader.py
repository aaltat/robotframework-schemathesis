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
from unittest.mock import MagicMock, Mock, patch

import pytest
from schemathesis import GenerationMode
from schemathesis.config import SchemathesisConfig
from schemathesis.core.result import Ok

from src.SchemathesisLibrary.schemathesisreader import Options, SchemathesisReader

DEFAULT_MAX_EXAMPLES = 100
CONFIG_MAX_EXAMPLES_50 = 50
CONFIG_MAX_EXAMPLES_750 = 750
# CONFIG_MAX_EXAMPLES_100 = 100


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


@patch("src.SchemathesisLibrary.schemathesisreader.SchemathesisConfig.discover")
def test_load_config_no_config_file_uses_defaults(mock_discover: Mock, mock_reader_config: Mock) -> None:
    mock_config = Mock(spec=SchemathesisConfig)
    mock_config.config_path = None
    mock_discover.return_value = mock_config
    reader = SchemathesisReader(mock_reader_config)
    reader.options = Options(max_examples=DEFAULT_MAX_EXAMPLES)

    config, generation_mode = reader._load_config()
    assert config == mock_config
    assert generation_mode == GenerationMode.POSITIVE
    assert reader.options.max_examples == DEFAULT_MAX_EXAMPLES


@patch("src.SchemathesisLibrary.schemathesisreader.SchemathesisConfig.discover")
def test_load_config_with_max_examples_in_config(mock_discover: Mock, mock_reader_config: Mock) -> None:
    mock_config = Mock(spec=SchemathesisConfig)
    mock_config.config_path = Path("schemathesis.toml")
    mock_generation = Mock()
    mock_generation.max_examples = CONFIG_MAX_EXAMPLES_50
    mock_generation.modes = None
    mock_config.projects.default.generation = mock_generation
    mock_discover.return_value = mock_config
    reader = SchemathesisReader(mock_reader_config)
    reader.options = Options(max_examples=DEFAULT_MAX_EXAMPLES)

    config, generation_mode = reader._load_config()
    assert config == mock_config
    assert generation_mode == GenerationMode.POSITIVE
    assert reader.options.max_examples == CONFIG_MAX_EXAMPLES_50


@patch("src.SchemathesisLibrary.schemathesisreader.SchemathesisConfig.discover")
def test_load_config_with_generation_mode_in_config(mock_discover: Mock, mock_reader_config: Mock) -> None:
    mock_config = Mock(spec=SchemathesisConfig)
    mock_config.config_path = Path("schemathesis.toml")
    mock_generation = Mock()
    mock_generation.max_examples = None
    mock_generation.modes = [GenerationMode.NEGATIVE]
    mock_config.projects.default.generation = mock_generation
    mock_discover.return_value = mock_config
    reader = SchemathesisReader(mock_reader_config)
    reader.options = Options(max_examples=DEFAULT_MAX_EXAMPLES)

    config, generation_mode = reader._load_config()
    assert config == mock_config
    assert generation_mode == GenerationMode.NEGATIVE
    assert reader.options.max_examples == DEFAULT_MAX_EXAMPLES  # Unchanged


@patch("src.SchemathesisLibrary.schemathesisreader.SchemathesisConfig.discover")
def test_load_config_with_both_max_examples_and_modes(mock_discover: Mock, mock_reader_config: Mock) -> None:
    mock_config = Mock(spec=SchemathesisConfig)
    mock_config.config_path = Path("schemathesis.toml")
    mock_generation = Mock()
    mock_generation.max_examples = CONFIG_MAX_EXAMPLES_750
    mock_generation.modes = [GenerationMode.NEGATIVE, GenerationMode.POSITIVE]
    mock_config.projects.default.generation = mock_generation
    mock_discover.return_value = mock_config
    reader = SchemathesisReader(mock_reader_config)
    reader.options = Options(max_examples=DEFAULT_MAX_EXAMPLES)

    config, generation_mode = reader._load_config()
    assert config == mock_config
    assert generation_mode == GenerationMode.NEGATIVE
    assert reader.options.max_examples == CONFIG_MAX_EXAMPLES_750


@patch("src.SchemathesisLibrary.schemathesisreader.SchemathesisConfig.discover")
def test_load_config_with_empty_modes_list(mock_discover: Mock, mock_reader_config: Mock) -> None:
    mock_config = Mock(spec=SchemathesisConfig)
    mock_config.config_path = Path("schemathesis.toml")
    mock_generation = Mock()
    mock_generation.max_examples = None
    mock_generation.modes = []
    mock_config.projects.default.generation = mock_generation
    mock_discover.return_value = mock_config
    reader = SchemathesisReader(mock_reader_config)
    reader.options = Options(max_examples=DEFAULT_MAX_EXAMPLES)

    config, generation_mode = reader._load_config()
    assert generation_mode == GenerationMode.POSITIVE
    assert config == mock_config


@patch("src.SchemathesisLibrary.schemathesisreader.SchemathesisConfig.discover")
def test_load_config_with_max_examples_zero(mock_discover: Mock, mock_reader_config: Mock) -> None:
    mock_config = Mock(spec=SchemathesisConfig)
    mock_config.config_path = Path("schemathesis.toml")
    mock_generation = Mock()
    mock_generation.max_examples = None
    mock_generation.modes = None
    mock_config.projects.default.generation = mock_generation
    mock_discover.return_value = mock_config
    reader = SchemathesisReader(mock_reader_config)
    reader.options = Options(max_examples=DEFAULT_MAX_EXAMPLES)
    reader._load_config()
    assert reader.options.max_examples == DEFAULT_MAX_EXAMPLES  # Not updated because config value is None


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
