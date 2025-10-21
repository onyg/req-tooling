import os
import json
import pytest
from unittest.mock import MagicMock, patch, mock_open
from igtools.specifications.releasenotes import ReleaseNoteManager
from igtools.errors import ReleaseNotesOutputPathNotExists
from igtools.specifications.data import Requirement, Release


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.releases = ["1.0.0", "1.1.0"]
    return config


@pytest.fixture
def manager(mock_config):
    return ReleaseNoteManager(config=mock_config)


def test_generate_creates_release_notes(tmp_path, manager, mock_config):
    mock_config.releases = ["1.0.0"]

    # Simulated non-stable requirement
    req1 = Requirement(key="REQ-1", title="Test", actor="Dev", version=1, conformance="SHALL", status="ACTIVE")
    req1.release_status = "MODIFIED"
    req1.source = "some/path.md"

    req2 = Requirement(key="REQ-2", title="Other", actor="OPS", version=1)
    req2.release_status = "STABLE"  # should be skipped

    rel = Release(name="Demo", version="1.0.0")
    rel.requirements = [req1, req2]

    # Patch dependencies
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open()) as mock_file, \
         patch("igtools.specifications.releasenotes.convert_to_link", return_value="some/path.html"), \
         patch.object(manager.release_manager, "load_version", return_value=rel):

        output_dir = tmp_path
        manager.generate(str(output_dir))

        handle = mock_file()
        handle.write.assert_called()

        # Read the written JSON from write() call
        written_content = "".join(call.args[0] for call in handle.write.call_args_list)
        data = json.loads(written_content)

        assert "releases" in data
        assert len(data["releases"]) == 1
        assert data["releases"][0]["version"] == "1.0.0"
        assert data["releases"][0]["requirements"][0]["key"] == "REQ-1"
        assert data["releases"][0]["requirements"][0]["path"] == "some/path.html"


def test_generate_skips_stable_in_later_release(tmp_path, manager, mock_config):
    # Requirement ist in 1.0.0 NEW, in 1.1.0 dann STABLE
    req_v1 = Requirement(key="REQ-NEW", title="Something", actor="Dev", version=1, conformance="SHOULD", status="ACTIVE")
    req_v1.release_status = "NEW"
    req_v1.source = "source.md"

    req_v2 = Requirement(key="REQ-NEW", title="Something", actor="Dev", version=1, conformance="SHOULD", status="ACTIVE")
    req_v2.release_status = "STABLE"
    req_v2.source = "source.md"

    # Release-Objekte für beide Versionen
    release_1_0 = Release(name="Demo", version="1.0.0")
    release_1_0.requirements = [req_v1]

    release_1_1 = Release(name="Demo", version="1.1.0")
    release_1_1.requirements = [req_v2]

    # Reihenfolge ist wichtig (wird reversed in JSON!)
    def load_version_mock(version):
        return {"1.0.0": release_1_0, "1.1.0": release_1_1}[version]

    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open()) as mock_file, \
         patch("igtools.specifications.releasenotes.convert_to_link", return_value="source.html"), \
         patch.object(manager.release_manager, "load_version", side_effect=load_version_mock):

        manager.generate(str(tmp_path))

        handle = mock_file()
        written_json = "".join(call.args[0] for call in handle.write.call_args_list)
        data = json.loads(written_json)

        # Releases sind reversed → 1.1.0 zuerst, dann 1.0.0
        assert data["releases"][0]["version"] == "1.1.0"
        assert data["releases"][0]["requirements"] == []  # STABLE: leer

        assert data["releases"][1]["version"] == "1.0.0"
        assert len(data["releases"][1]["requirements"]) == 1
        assert data["releases"][1]["requirements"][0]["key"] == "REQ-NEW"
        assert data["releases"][1]["requirements"][0]["release_status"] == "NEW"

    


def test_generate_raises_if_output_missing(manager):
    with patch("os.path.exists", return_value=False):
        with pytest.raises(ReleaseNotesOutputPathNotExists):
            manager.generate("/some/fake/path")
