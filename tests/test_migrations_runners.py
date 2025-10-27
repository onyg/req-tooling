import os
import json
import pytest

from typing import Iterable
from unittest.mock import patch, mock_open, MagicMock
from packaging.version import Version

from igtools.migrations.errors import MigrationError
from igtools.migrations.registry import MigrationRegistry
from igtools.migrations.runners import ensure_tool_not_older_than_config, validate_registry_against_tool_version, latest_registry_version


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.name = "Test Project"
    config.current = "1.2.0"
    config.releases = ["1.0.0", "1.1.0", "1.2.0"]
    config.migrated_with_version = Version("0.3.0")
    return config


def test_latest_registry_version():
    assert latest_registry_version(registry=MigrationRegistry.build()) == Version("0.3.0")


def test_ensure_tool_not_older_than_config_correct(mock_config):
    try:
        ensure_tool_not_older_than_config(config=mock_config, tool_version=Version("1.2.0"))
    except MigrationError as e:
        pytest.fail(f"Unexpected MigrationError raised: {e}")


def test_ensure_tool_not_older_than_config_incorrect(mock_config):
    mock_config.migrated_with_version = Version("1.2.1")
    with pytest.raises(MigrationError):
        ensure_tool_not_older_than_config(config=mock_config, tool_version=Version("1.2.0"))


def test_validate_registry_against_tool_version_correct(mock_config):
    try:
        validate_registry_against_tool_version(registry=MigrationRegistry.build(), tool_version=Version("1.2.0"))
    except MigrationError as e:
        pytest.fail(f"Unexpected MigrationError raised: {e}")


def test_validate_registry_against_tool_version_icorrect(mock_config):
    with pytest.raises(MigrationError):
        validate_registry_against_tool_version(registry=MigrationRegistry.build(), tool_version=Version("0.2.10"))

