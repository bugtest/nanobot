"""Test CLI commands."""

import shutil
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from nanobot.cli.commands import app
from nanobot.config.schema import Config

runner = CliRunner()


@pytest.fixture
def mock_paths():
    """Mock config/workspace paths for test isolation."""
    with patch("nanobot.config.loader.get_config_path") as mock_cp, \
         patch("nanobot.config.loader.save_config") as mock_sc, \
         patch("nanobot.config.loader.load_config") as mock_lc, \
         patch("nanobot.utils.helpers.get_workspace_path") as mock_ws:

        base_dir = Path("./test_onboard_data")
        if base_dir.exists():
            shutil.rmtree(base_dir)
        base_dir.mkdir()

        config_file = base_dir / "config.json"
        workspace_dir = base_dir / "workspace"

        mock_cp.return_value = config_file
        mock_ws.return_value = workspace_dir
        mock_sc.side_effect = lambda config: config_file.write_text("{}")

        yield config_file, workspace_dir

        if base_dir.exists():
            shutil.rmtree(base_dir)


def test_onboard_fresh_install(mock_paths):
    """No existing config — should create from scratch."""
    config_file, workspace_dir = mock_paths

    result = runner.invoke(app, ["onboard"])

    assert result.exit_code == 0
    assert "Created config" in result.stdout
    assert "Created workspace" in result.stdout
    assert "nanobot is ready" in result.stdout
    assert config_file.exists()


def test_onboard_existing_config_refresh(mock_paths):
    """Config exists, user declines overwrite — should refresh."""
    config_file, workspace_dir = mock_paths
    config_file.write_text('{"existing": true}')

    result = runner.invoke(app, ["onboard"], input="n\n")

    assert result.exit_code == 0
    assert "Config already exists" in result.stdout
    assert "keeping existing values" in result.stdout
    assert workspace_dir.exists()


def test_onboard_existing_config_overwrite(mock_paths):
    """Config exists, user confirms overwrite — should reset to defaults."""
    config_file, workspace_dir = mock_paths
    config_file.write_text('{"existing": true}')

    result = runner.invoke(app, ["onboard"], input="y\n")

    assert result.exit_code == 0
    assert "Config already exists" in result.stdout
    assert "Config reset to defaults" in result.stdout
    assert workspace_dir.exists()


def test_config_openrouter_provider():
    """Test OpenRouter provider configuration."""
    config = Config()
    config.providers.openrouter.api_key = "sk-or-v1-test"

    assert config.get_api_key() == "sk-or-v1-test"
    assert config.get_api_base() == "https://openrouter.ai/api/v1"


def test_config_custom_api_base():
    """Test custom API base URL."""
    config = Config()
    config.providers.openrouter.api_key = "sk-or-v1-test"
    config.providers.openrouter.api_base = "https://custom.api.com/v1"

    assert config.get_api_base() == "https://custom.api.com/v1"


def test_agent_defaults():
    """Test default agent configuration."""
    config = Config()

    assert config.agents.defaults.model == "openrouter/anthropic/claude-3-5-sonnet"
    assert config.agents.defaults.max_tokens == 8192
    assert config.agents.defaults.temperature == 0.7
    assert config.agents.defaults.max_tool_iterations == 20
    assert config.agents.defaults.memory_window == 50
