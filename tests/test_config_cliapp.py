import os
import tempfile
import yaml
import pytest
from unittest.mock import patch, mock_open

from igtools import config
from igtools.errors import ConfigPathNotExists



@pytest.fixture
def cli_app_config():
    return config.CliAppConfig()


def test_cli_app_config_process(cli_app_config):
    """
    Test the full process() flow by mocking input() calls and capturing print() outputs.
    """
    inputs = iter([
        "",         # config_path -> default (CONFIG_DEFAULT_DIR)
        "input",    # directory
        "ProjectX", # name
        "tST",      # prefix
        "pyt",      # scope
    ])

    def mock_input(prompt):
        return next(inputs)

    # Simulate content of an existing config.yaml
    yaml_content = yaml.dump({
        "directory": "old_input",
        "name": "ProjectNameOld",
        "prefix": "FOO",
        "scope": "SCO",
        "current": "1.0",
        "final": "0.9",
        "releases": ["0.9", "1.0"]
    })

    # Patch input(), print(), open(), os.makedirs(), os.path.exists()
    with patch("builtins.input", side_effect=mock_input), \
         patch("builtins.print") as mock_print, \
         patch("builtins.open", mock_open(read_data=yaml_content)) as mocked_open, \
         patch("os.makedirs") as mocked_makedirs, \
         patch("os.path.exists", return_value=True):

        # Check pre process config values
        config.config.load()
        assert config.config.directory == "old_input"
        assert config.config.name == "ProjectNameOld"
        assert config.config.prefix == "FOO"
        assert config.config.scope == "SCO"

        # Process the cli application
        cli_app_config.process()

        # Check config values
        assert config.config.directory == "input"
        assert config.config.name == "ProjectX"
        assert config.config.prefix == "TST"  # Should be uppercased
        assert config.config.scope == "PYT"   # Should be uppercased

        # Verify that save() was triggered (open called in write mode)
        mocked_open.assert_called()
        args, kwargs = mocked_open.call_args
        assert args[1] == 'w'


def test_cli_app_config_show(cli_app_config):
    """
    Test the show() method, capturing printed output.
    """
    config.config.name = "ProjectX"
    config.config.current = "1.0.0"
    config.config.final = "0.9.0"
    config.config.prefix = "TST"
    config.config.scope = "PYT"
    config.config.directory = "some/dir"

    with patch("builtins.print") as mock_print:
        cli_app_config.show()
        assert mock_print.called


def test_cli_app_config_show_current_release(cli_app_config):
    """
    Test the show_current_release() method, capturing printed output.
    """
    config.config.name = "ProjectX"
    config.config.current = "1.0.0"
    config.config.final = "0.9.0"
    config.config.releases = ["0.9.0", "1.0.0"]

    with patch("builtins.print") as mock_print:
        cli_app_config.show_current_release()
        assert mock_print.called
