import os
import tempfile
import yaml
import pytest

from igtools import config
from igtools.errors import ConfigPathNotExists


def test_set_filepath():
    c = config.Config()
    c.set_filepath("/some/path")
    assert c.path == "/some/path"


def test_add_release():
    c = config.Config()
    c.add_release("1.0.0")
    # Should not add duplicate
    c.add_release("1.0.0")
    assert c.releases == ["1.0.0"]


def test_to_dict_and_from_dict():
    c = config.Config()
    c.directory = "test"
    c.name = "Test Project"
    c.prefix = "TST"
    c.scope = "PYT"
    c.current = "1.0.0"
    c.final = "0.9.0"
    c.releases = ["0.9.0", "1.0.0"]

    d = c.to_dict()
    assert d["directory"] == "test"
    assert d["name"] == "Test Project"
    assert d["prefix"] == "TST"
    assert d["scope"] == "PYT"
    assert d["current"] == "1.0.0"
    assert d["final"] == "0.9.0"
    assert d["releases"] == ["0.9.0", "1.0.0"]

    new_config = config.Config()
    new_config.from_dict(d)
    assert new_config.to_dict() == d


def test_save_and_load():
    c = config.Config()
    c.directory = "test"
    c.name = "Test Project"
    c.prefix = "TST"
    c.scope = "PYT"
    c.current = "1.0.0"
    c.final = "0.9.0"
    c.releases = ["0.9.0", "1.0.0"]

    # Create a temporary directory for safe file operations
    with tempfile.TemporaryDirectory() as tempdir:
        c.set_filepath(tempdir)
        c.save()

        # Config file was created
        config_filepath = os.path.join(tempdir, "config.yaml")
        assert os.path.exists(config_filepath)

        # Load the configuration from the file
        loaded_config = config.Config()
        loaded_config.set_filepath(tempdir)
        loaded_config.load()

        # Verify that loaded config matches original
        assert loaded_config.to_dict() == c.to_dict()


def test_load_missing_file_raises():
    c = config.Config()
    with tempfile.TemporaryDirectory() as tempdir:
        c.set_filepath(tempdir)
        # Create a temporary directory but do NOT create a config.yaml file
        with pytest.raises(ConfigPathNotExists):
            # Trying to load should raise ConfigPathNotExists
            c.load()
