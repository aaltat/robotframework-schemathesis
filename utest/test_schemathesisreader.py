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

from schemathesisreader import Options, SchemathesisReader  # type: ignore[import-not-found]

# Test constants
DEFAULT_MAX_EXAMPLES = 10
CONFIG_MAX_EXAMPLES_50 = 50
CONFIG_MAX_EXAMPLES_75 = 75
CONFIG_MAX_EXAMPLES_100 = 100


def create_mock_reader_config() -> Mock:
    """Create a mock ReaderConfig object with necessary attributes."""
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
    mock_config.kwargs = {}  # Empty dict, not a Mock
    return mock_config


class TestLoadConfig:
    """Unit tests for SchemathesisReader._load_config method."""

    @patch("schemathesisreader.SchemathesisConfig.discover")
    def test_load_config_no_config_file_uses_defaults(self, mock_discover: Mock) -> None:
        """Test that when no config file exists, defaults are used."""
        # Mock config with no config_path
        mock_config = Mock(spec=SchemathesisConfig)
        mock_config.config_path = None
        mock_discover.return_value = mock_config

        reader = SchemathesisReader(create_mock_reader_config())
        reader.options = Options(max_examples=DEFAULT_MAX_EXAMPLES)

        config, generation_mode = reader._load_config()

        assert config == mock_config
        assert generation_mode == GenerationMode.POSITIVE
        assert reader.options.max_examples == DEFAULT_MAX_EXAMPLES  # Unchanged

    @patch("schemathesisreader.SchemathesisConfig.discover")
    def test_load_config_with_max_examples_in_config(self, mock_discover: Mock) -> None:
        """Test that max_examples from config overrides instance options."""
        # Mock config with max_examples
        mock_config = Mock(spec=SchemathesisConfig)
        mock_config.config_path = Path("schemathesis.toml")
        mock_generation = Mock()
        mock_generation.max_examples = CONFIG_MAX_EXAMPLES_50
        mock_generation.modes = None
        mock_config.projects.default.generation = mock_generation
        mock_discover.return_value = mock_config

        reader = SchemathesisReader(create_mock_reader_config())
        reader.options = Options(max_examples=DEFAULT_MAX_EXAMPLES)

        config, generation_mode = reader._load_config()

        assert config == mock_config
        assert generation_mode == GenerationMode.POSITIVE
        assert reader.options.max_examples == CONFIG_MAX_EXAMPLES_50  # Updated from config

    @patch("schemathesisreader.SchemathesisConfig.discover")
    def test_load_config_with_generation_mode_in_config(self, mock_discover: Mock) -> None:
        """Test that generation mode is extracted from config."""
        # Mock config with generation modes
        mock_config = Mock(spec=SchemathesisConfig)
        mock_config.config_path = Path("schemathesis.toml")
        mock_generation = Mock()
        mock_generation.max_examples = None
        mock_generation.modes = [GenerationMode.NEGATIVE]
        mock_config.projects.default.generation = mock_generation
        mock_discover.return_value = mock_config

        reader = SchemathesisReader(create_mock_reader_config())
        reader.options = Options(max_examples=DEFAULT_MAX_EXAMPLES)

        config, generation_mode = reader._load_config()

        assert config == mock_config
        assert generation_mode == GenerationMode.NEGATIVE
        assert reader.options.max_examples == DEFAULT_MAX_EXAMPLES  # Unchanged

    @patch("schemathesisreader.SchemathesisConfig.discover")
    def test_load_config_with_both_max_examples_and_modes(self, mock_discover: Mock) -> None:
        """Test that both max_examples and generation mode are applied from config."""
        # Mock config with both settings
        mock_config = Mock(spec=SchemathesisConfig)
        mock_config.config_path = Path("schemathesis.toml")
        mock_generation = Mock()
        mock_generation.max_examples = CONFIG_MAX_EXAMPLES_100
        mock_generation.modes = [GenerationMode.NEGATIVE, GenerationMode.POSITIVE]
        mock_config.projects.default.generation = mock_generation
        mock_discover.return_value = mock_config

        reader = SchemathesisReader(create_mock_reader_config())
        reader.options = Options(max_examples=DEFAULT_MAX_EXAMPLES)

        config, generation_mode = reader._load_config()

        assert config == mock_config
        assert generation_mode == GenerationMode.NEGATIVE  # First mode
        assert reader.options.max_examples == CONFIG_MAX_EXAMPLES_100  # Updated from config

    @patch("schemathesisreader.SchemathesisConfig.discover")
    def test_load_config_with_empty_modes_list(self, mock_discover: Mock) -> None:
        """Test that empty modes list falls back to default POSITIVE mode."""
        # Mock config with empty modes list
        mock_config = Mock(spec=SchemathesisConfig)
        mock_config.config_path = Path("schemathesis.toml")
        mock_generation = Mock()
        mock_generation.max_examples = None
        mock_generation.modes = []
        mock_config.projects.default.generation = mock_generation
        mock_discover.return_value = mock_config

        reader = SchemathesisReader(create_mock_reader_config())
        reader.options = Options(max_examples=DEFAULT_MAX_EXAMPLES)

        _, generation_mode = reader._load_config()

        assert generation_mode == GenerationMode.POSITIVE

    @patch("schemathesisreader.SchemathesisConfig.discover")
    def test_load_config_with_no_generation_section(self, mock_discover: Mock) -> None:
        """Test that missing generation section uses defaults."""
        # Mock config with no generation section
        mock_config = Mock(spec=SchemathesisConfig)
        mock_config.config_path = Path("schemathesis.toml")
        mock_config.projects.default.generation = None
        mock_discover.return_value = mock_config

        reader = SchemathesisReader(create_mock_reader_config())
        reader.options = Options(max_examples=DEFAULT_MAX_EXAMPLES)

        config, generation_mode = reader._load_config()

        assert config == mock_config
        assert generation_mode == GenerationMode.POSITIVE
        assert reader.options.max_examples == DEFAULT_MAX_EXAMPLES  # Unchanged

    @patch("schemathesisreader.SchemathesisConfig.discover")
    def test_load_config_with_max_examples_zero(self, mock_discover: Mock) -> None:
        """Test that max_examples=0 in config is treated as None (not applied)."""
        # Mock config with max_examples explicitly set to None
        mock_config = Mock(spec=SchemathesisConfig)
        mock_config.config_path = Path("schemathesis.toml")
        mock_generation = Mock()
        mock_generation.max_examples = None
        mock_generation.modes = None
        mock_config.projects.default.generation = mock_generation
        mock_discover.return_value = mock_config

        reader = SchemathesisReader(create_mock_reader_config())
        reader.options = Options(max_examples=DEFAULT_MAX_EXAMPLES)

        reader._load_config()

        assert reader.options.max_examples == DEFAULT_MAX_EXAMPLES  # Not updated because config value is None


class TestGetDataFromSourceConfigIntegration:
    """Integration tests for how _load_config is used in get_data_from_source."""

    def test_get_data_from_source_raises_value_error_when_options_not_set(self) -> None:
        """Test that get_data_from_source raises ValueError when options is None."""
        reader = SchemathesisReader(create_mock_reader_config())
        reader.options = None

        with pytest.raises(ValueError, match="Options must be set before calling get_data_from_source"):
            reader.get_data_from_source()

    @patch("schemathesisreader.openapi.from_path")
    @patch("schemathesisreader.SchemathesisConfig.discover")
    def test_get_data_from_source_passes_config_to_schema_loader(
        self, mock_discover: Mock, mock_from_path: Mock
    ) -> None:
        """Test that config returned by _load_config is passed to schema loader."""
        # Setup mocks
        mock_config = Mock(spec=SchemathesisConfig)
        mock_config.config_path = None
        mock_discover.return_value = mock_config

        mock_schema = MagicMock()
        mock_schema.get_all_operations.return_value = []
        mock_from_path.return_value = mock_schema

        # Create reader with valid file path
        reader = SchemathesisReader(create_mock_reader_config())
        test_file = Path(__file__)  # Use this file as a valid path
        reader.options = Options(max_examples=DEFAULT_MAX_EXAMPLES, path=test_file)

        # Execute
        reader.get_data_from_source()

        # Verify config was passed to from_path
        mock_from_path.assert_called_once_with(test_file, config=mock_config)

    @patch("schemathesisreader.openapi.from_url")
    @patch("schemathesisreader.SchemathesisConfig.discover")
    def test_get_data_from_source_uses_generation_mode_from_config(
        self, mock_discover: Mock, mock_from_url: Mock
    ) -> None:
        """Test that generation_mode from _load_config is used in strategy creation."""
        # Setup config with NEGATIVE mode
        mock_config = Mock(spec=SchemathesisConfig)
        mock_config.config_path = Path("schemathesis.toml")
        mock_generation = Mock()
        mock_generation.max_examples = None
        mock_generation.modes = [GenerationMode.NEGATIVE]
        mock_config.projects.default.generation = mock_generation
        mock_discover.return_value = mock_config

        # Setup schema with one operation
        mock_operation = Mock()
        mock_strategy = Mock()
        mock_strategy.map.return_value = mock_strategy
        mock_operation.ok.return_value.as_strategy.return_value = mock_strategy

        mock_ok_result = Mock(spec=Ok)
        mock_ok_result.ok.return_value = mock_operation.ok.return_value

        mock_schema = Mock()
        mock_schema.get_all_operations.return_value = [mock_ok_result]
        mock_from_url.return_value = mock_schema

        reader = SchemathesisReader(create_mock_reader_config())
        reader.options = Options(max_examples=DEFAULT_MAX_EXAMPLES, url="http://example.com/schema")

        # Execute
        with patch("schemathesisreader.add_examples"):
            reader.get_data_from_source()

        # Verify as_strategy was called with NEGATIVE mode
        mock_operation.ok.return_value.as_strategy.assert_called_once_with(
            generation_mode=GenerationMode.NEGATIVE
        )

    @patch("schemathesisreader.openapi.from_path")
    @patch("schemathesisreader.add_examples")
    @patch("schemathesisreader.SchemathesisConfig.discover")
    def test_get_data_from_source_uses_updated_max_examples_from_config(
        self, mock_discover: Mock, mock_add_examples: Mock, mock_from_path: Mock
    ) -> None:
        """Test that max_examples updated by _load_config is used in add_examples."""
        # Setup config with max_examples=75
        mock_config = Mock(spec=SchemathesisConfig)
        mock_config.config_path = Path("schemathesis.toml")
        mock_generation = Mock()
        mock_generation.max_examples = CONFIG_MAX_EXAMPLES_75
        mock_generation.modes = None
        mock_config.projects.default.generation = mock_generation
        mock_discover.return_value = mock_config

        # Setup schema with one operation
        mock_operation = Mock()
        mock_strategy = Mock()
        mock_strategy.map.return_value = mock_strategy
        mock_operation.ok.return_value.as_strategy.return_value = mock_strategy

        mock_ok_result = Mock(spec=Ok)
        mock_ok_result.ok.return_value = mock_operation.ok.return_value

        mock_schema = Mock()
        mock_schema.get_all_operations.return_value = [mock_ok_result]
        mock_from_path.return_value = mock_schema

        reader = SchemathesisReader(create_mock_reader_config())
        test_file = Path(__file__)
        reader.options = Options(max_examples=DEFAULT_MAX_EXAMPLES, path=test_file)

        # Execute
        reader.get_data_from_source()

        # Verify add_examples was called with updated max_examples=75
        assert mock_add_examples.call_count == 1
        call_args = mock_add_examples.call_args
        assert call_args[0][2] == CONFIG_MAX_EXAMPLES_75  # Third argument should be max_examples

    def test_get_data_from_source_raises_value_error_for_invalid_path(self) -> None:
        """Test that get_data_from_source raises ValueError for non-existent file."""
        reader = SchemathesisReader(create_mock_reader_config())
        invalid_path = Path("/nonexistent/file.yaml")
        reader.options = Options(max_examples=DEFAULT_MAX_EXAMPLES, path=invalid_path)

        with pytest.raises(ValueError, match="Provided path .* is not a valid file"):
            reader.get_data_from_source()

    def test_get_data_from_source_raises_value_error_when_no_path_or_url(self) -> None:
        """Test that get_data_from_source raises ValueError when neither path nor url is provided."""
        reader = SchemathesisReader(create_mock_reader_config())
        reader.options = Options(max_examples=DEFAULT_MAX_EXAMPLES)

        with patch("schemathesisreader.SchemathesisConfig.discover"), pytest.raises(
            ValueError, match="Either 'url' or 'path' must be provided"
        ):
            reader.get_data_from_source()
