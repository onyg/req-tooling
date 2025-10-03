import os
import json
import pytest
from unittest.mock import patch, mock_open, MagicMock
from igtools.specifications.exporter import RequirementExporter
from igtools.specifications.data import Requirement, Release
from igtools.errors import ExportFormatUnknown, ReleaseNotesOutputPathNotExists


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.name = "Test Project"
    config.current = "1.0.0"
    config.releases = ["1.0.0"]
    return config


def test_export_writes_json_file(tmp_path, mock_config):

    req = Requirement(
        key="REQ-1",
        title="Exported requirement",
        actor="EPA-PS",
        version=1,
        conformance="SHALL",
        status="ACTIVE",
        source="file.md",
        test_procedures={"EPA-PS":["AN01"]}
    )
    req.release_status = "MODIFIED"
    req.text = "This must be exported"
    req.is_deleted = False

    release = Release(name="Test Project", version="1.0.0")
    release.requirements = [req]

    exporter = RequirementExporter(config=mock_config, format="JSON")

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
        assert data[0]["key"] == "REQ-1"
        assert data[0]["path"] == "file.html"
        assert data[0]["text"] == "This must be exported"
        assert data[0]["title"] == "Exported requirement"
        assert data[0]["version"] == 1
        assert data[0]["test_procedures"] == {"EPA-PS":["AN01"]}
        assert data[0]["content_hash"] == "3d762a0c0bcac7a3237a6ed44435c9bbb260ef533b964fa2d26fe774815ae5e6"


def test_export_skips_deleted_requirements(tmp_path, mock_config):
    req = Requirement(key="REQ-2")
    req.is_deleted = True

    release = Release(name="Demo", version="1.0.0")
    release.requirements = [req]

    exporter = RequirementExporter(config=mock_config, format="JSON")

    with patch.object(exporter.release_manager, "load", return_value=release), \
         patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open()) as mocked_file, \
         patch("igtools.specifications.exporter.convert_to_link", return_value="dummy.html"):

        exporter.export(str(tmp_path))
        handle = mocked_file()
        written = "".join(call.args[0] for call in handle.write.call_args_list)
        data = json.loads(written)

        assert data == []


def test_export_raises_if_output_missing(mock_config):
    exporter = RequirementExporter(config=mock_config, format="JSON")

    with patch("os.path.exists", return_value=False):
        with pytest.raises(ReleaseNotesOutputPathNotExists):
            exporter.export("/some/missing/path")


def test_export_raises_for_unknown_format(tmp_path, mock_config):
    exporter = RequirementExporter(config=mock_config, format="XML")

    with patch("os.path.exists", return_value=True):
        with pytest.raises(ExportFormatUnknown):
            exporter.save_export(tmp_path, data=[])


def test_export_outputs_full_data_structure(tmp_path, mock_config):
    req = Requirement(
        key="REQ-100",
        title="Complete Export",
        actor="EPA-PS, EPA-FdV",
        version=3,
        conformance="MAY",
        status="RETIRED",
        source="path/to/requirement.md",
        test_procedures={"EPA-PS":[], "EPA-FdV":["AN00", "AN001"]}
    )
    req.release_status = "MODIFIED"
    req.text = "Detailed requirement text."
    req.is_deleted = False
    release = Release(name="BigProject", version="3.1.0")
    release.requirements = [req]

    expected_data = [{
        "key": "REQ-100",
        "title": "Complete Export",
        "actor": ["EPA-FdV", "EPA-PS"],
        "version": 3,
        "release_status": "MODIFIED",
        "status": "RETIRED",
        "source": "path/to/requirement.md",
        "text": "Detailed requirement text.",
        "conformance": "MAY",
        "created": req._created,
        "modified": req._modified,
        "date": req._date,
        "path": "path/to/requirement.html",
        "release": "3.1.0",
        "test_procedures": {"EPA-PS":[], "EPA-FdV":["AN00", "AN001"]},
        "content_hash": "ed249a239548b17fbe73641b17a2f7ff6acde485115dc7a883534e759277383a"
    }]

    exporter = RequirementExporter(config=mock_config, format="JSON")

    with patch.object(exporter.release_manager, "load", return_value=release), \
         patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open()) as mocked_file, \
         patch("igtools.specifications.exporter.convert_to_link", return_value="path/to/requirement.html"):

        exporter.export(str(tmp_path))

        handle = mocked_file()
        written = "".join(call.args[0] for call in handle.write.call_args_list)
        data = json.loads(written)

        assert data == expected_data

