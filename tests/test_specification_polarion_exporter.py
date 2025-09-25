import os
import json
import pytest
from unittest.mock import patch, mock_open, MagicMock
from igtools.specifications.polarion import PolarionExporter
from igtools.specifications.data import Requirement, Release
from igtools.errors import ExportFormatUnknown, ReleaseNotesOutputPathNotExists, FilePathNotExists


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.name = "Test Project"
    config.current = "1.0.0"
    config.releases = ["1.0.0"]
    return config

@pytest.fixture
def mock_ig_config():
    config = MagicMock()
    config.name = "gemIGTestProjekt"
    config.title = "Test Project IG"
    config.canonical = "https://www.example.com"
    config.version = "1.0.0"
    config.link = "https://www.example.com/1.0.0"
    return config


def test_polarion_export_writes_json_file(tmp_path, mock_config, mock_ig_config):

    req = Requirement(
        key="REQ-1",
        title="Exported requirement",
        actor="EPA-PS",
        version=0,
        conformance="SHALL",
        status="ACTIVE",
        source="file.md"
    )
    req.release_status = "MODIFIED"
    req.text = "This must be exported"
    req.is_deleted = False

    release = Release(name="Test Project", version="1.0.0")
    release.requirements = [req]

    exporter = PolarionExporter(config=mock_config, ig_config=mock_ig_config)

    with patch.object(exporter.release_manager, "load", return_value=release), \
         patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open()) as mocked_file, \
         patch("igtools.specifications.exporter.convert_to_link", return_value="file.html"):

        exporter.export(str(tmp_path))

        handle = mocked_file()
        written_json = "".join(call.args[0] for call in handle.write.call_args_list)
        data = json.loads(written_json)

        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["document_id"] == "gemIGTestProjekt"
        assert data[0]["document_title"] == "Test Project IG"
        assert data[0]["document_link"] == "https://www.example.com/1.0.0"
        assert data[0]["key"] == "REQ-1"
        assert data[0]["text"] == "This must be exported"
        assert data[0]["title"] == "Exported requirement"
        assert data[0]["version"] == 0
        assert data[0]["status"] == "ACTIVE"
        assert data[0]["conformance"] == "SHALL"
        assert data[0]["link"] == "https://www.example.com/1.0.0/file.html#REQ-1"
        assert data[0]["product_types"] == []


def test_polarion_export_skips_deleted_requirements(tmp_path, mock_config, mock_ig_config):
    req = Requirement(
        key="REQ-1",
        title="Exported requirement",
        actor="EPA-PS",
        version=1,
        conformance="SHALL",
        status="ACTIVE",
        source="file.md"
    )
    req.text = "This must be exported"
    req.is_deleted = True

    release = Release(name="Demo", version="1.0.0")
    release.requirements = [req]

    exporter = PolarionExporter(config=mock_config, ig_config=mock_ig_config)

    with patch.object(exporter.release_manager, "load", return_value=release), \
         patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open()) as mocked_file, \
         patch("igtools.specifications.exporter.convert_to_link", return_value="dummy.html"):

        exporter.export(str(tmp_path))
        handle = mocked_file()
        written = "".join(call.args[0] for call in handle.write.call_args_list)
        data = json.loads(written)

        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["document_id"] == "gemIGTestProjekt"
        assert data[0]["document_title"] == "Test Project IG"
        assert data[0]["document_link"] == "https://www.example.com/1.0.0"
        assert data[0]["key"] == "REQ-1"
        assert data[0]["text"] == "This must be exported"
        assert data[0]["title"] == "Exported requirement"
        assert data[0]["version"] == 1
        assert data[0]["status"] == "RETIRED"
        assert data[0]["conformance"] == "SHALL"
        assert data[0]["link"] == "https://www.example.com/1.0.0/file.html#REQ-1-01"
        assert data[0]["product_types"] == []


def test_polarion_export_raises_if_output_missing(mock_config, mock_ig_config):
    exporter = PolarionExporter(config=mock_config, ig_config=mock_ig_config)

    with patch("os.path.exists", return_value=False):
        with pytest.raises(FilePathNotExists):
            exporter.export("/some/missing/path")



def test_polarion_export_outputs_full_data_structure(tmp_path, mock_config, mock_ig_config):
    req = Requirement(
        key="REQ-100",
        title="Complete Export",
        actor="EPA-PS, EPA-FdV",
        version=3,
        conformance="MAY",
        status="RETIRED",
        source="path/to/requirement.md"
    )
    req.release_status = "MODIFIED"
    req.text = "Detailed requirement text."
    req.is_deleted = False
    release = Release(name="BigProject", version="3.1.0")
    release.requirements = [req]

    expected_data = [{
        "document_id": "gemIGTestProjekt",
        "document_title": "Test Project IG",
        "document_link": "https://www.example.com/1.0.0",
        "key": "REQ-100",
        "title": "Complete Export",
        "product_types": [],
        "version": 3,
        "status": "RETIRED",
        "link": "https://www.example.com/1.0.0/requirement.html#REQ-100-03",
        "text": "Detailed requirement text.",
        "conformance": "MAY"
    }]

    exporter = PolarionExporter(config=mock_config, ig_config=mock_ig_config)

    with patch.object(exporter.release_manager, "load", return_value=release), \
         patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open()) as mocked_file, \
         patch("igtools.specifications.exporter.convert_to_link", return_value="requirement.html"):

        exporter.export(str(tmp_path))

        handle = mocked_file()
        written = "".join(call.args[0] for call in handle.write.call_args_list)
        data = json.loads(written)

        assert data == expected_data
