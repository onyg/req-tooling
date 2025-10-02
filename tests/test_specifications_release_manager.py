import os
import pytest
from unittest.mock import patch, mock_open, MagicMock
from igtools.config import CONFIG_DEFAULT_DIR
from igtools.specifications.release import ReleaseManager
from igtools.specifications.data import Release, Requirement
from igtools.errors import (
    ReleaseAlreadyExistsException, NoReleaseVersionSetException,
    ReleaseNotFoundException, FinalReleaseException
)


@pytest.fixture
def mock_config():
    return MagicMock(
        path=CONFIG_DEFAULT_DIR,
        name="Test Project",
        current="1.0.0",
        releases=["1.0.0"],
        frozen_version=None,
        add_release=MagicMock(),
        save=MagicMock()
    )


@pytest.fixture
def manager(mock_config):
    return ReleaseManager(mock_config)


@pytest.fixture
def directory():
    return CONFIG_DEFAULT_DIR


def test_release_manager_directory(manager):
    assert manager.directory == ".igtools/releases"


def test_release_directory(manager):
    assert manager.release_directory("1.0.0") == ".igtools/releases/1_0_0"


def test_archive_directory(manager):
    assert manager.archive_directory() == ".igtools/releases/archive"


def test_check_new_version_ok(manager):
    with patch("os.path.exists", return_value=False):
        assert manager.check_new_version("1.0.1") is True


def test_check_new_version_exists(manager):
    with patch("os.path.exists", return_value=True):
        with pytest.raises(ReleaseAlreadyExistsException):
            manager.check_new_version("1.0.0")


def test_save_anddelete_requirement(manager, directory):
    req = Requirement(key="REQ-TST01234A23")
    req.for_deletion = True
    with patch("os.path.exists", return_value=True), \
         patch("os.remove") as mock_remove:
        manager.delete_requirement(req, directory)
        mock_remove.assert_called_once_with(f"{directory}/REQ-TST01234A23.yaml")


def testsave_requirement(manager, directory):
    req = Requirement(key="REQ-TST01234A23", title="Test")
    with patch("builtins.open", mock_open()) as mocked_file:
        manager.save_requirement(req, directory)
        mocked_file.assert_called_once_with(f"{directory}/REQ-TST01234A23.yaml", 'w', encoding='utf-8')


def test_freeze_release_success(manager):
    with patch("os.path.exists", return_value=True), \
         patch("os.listdir", return_value=[f"REQ-TST01234A23.yaml"]), \
         patch("builtins.open", mock_open()) as mocked_file:
        manager.freeze_release()
        
        manager.config.save.assert_called_once()
        assert manager.config.frozen_version == manager.config.current


def test_freeze_release_no_version(manager):
    manager.config.current = None
    with pytest.raises(NoReleaseVersionSetException):
        manager.freeze_release()


def test_freeze_release_not_found(manager):
    with patch("os.path.exists", return_value=False):
        with pytest.raises(ReleaseNotFoundException):
            manager.freeze_release()


def test_freeze_release_true(manager):
    manager.config.frozen_version = "1.0.0"
    assert manager.is_current_release_frozen() is True


def test_is_current_freeze_false(manager):
    manager.config.frozen_version = "1.2.0"
    assert manager.is_current_release_frozen() is False


def test_check_freeze_raises(manager):
    manager.config.frozen_version = "1.0.0"
    assert manager.is_current_release_frozen() is True


def test_load_version_returns_release(manager):
    with patch.object(manager, '_load_requirements', return_value=[Requirement(key="REQ-TST01234A23")]):
        release = manager.load_version("1.0.0")
        assert isinstance(release, Release)
        assert len(release.requirements) == 1
        assert release.requirements[0].key == "REQ-TST01234A23"
