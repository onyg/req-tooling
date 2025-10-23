import os
import json
import pytest
import calendar

from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime, date, timezone, timedelta

from igtools.polarion.polarion import PolarionExporter, PolarionExportError, convert_polarion_date_export, PolarionExportDateError
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
    config.date = "2025-09-12"
    return config


def test_polarion_export_writes_json_file(tmp_path, mock_config, mock_ig_config):

    req = Requirement(
        key="REQ-1",
        title="Exported requirement",
        actor="ACTOR",
        version=0,
        conformance="SHALL",
        status="ACTIVE",
        source="file.md",
        test_procedures={"ACTOR":["AN01"]}
    )
    req.release_status = "MODIFIED"
    req.text = "This must be exported"
    req.is_deleted = False

    release = Release(name="Test Project", version="1.0.0")
    release.requirements = [req]

    fake_actor_map   = {"ACTOR": "ProductTypeB"}
    fake_testproc_map = {"AN01": "TP-456"}

    exporter = PolarionExporter(config=mock_config, ig_config=mock_ig_config)

    with patch.object(exporter.release_manager, "load", return_value=release), \
         patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open()) as mocked_file, \
         patch("igtools.specifications.exporter.convert_to_link", return_value="file.html"), \
         patch("igtools.polarion.polarion.load_polarion_mappings", return_value=(fake_actor_map, fake_testproc_map)):

        exporter.export(str(tmp_path))

        handle = mocked_file()
        written_json = "".join(call.args[0] for call in handle.write.call_args_list)
        data = json.loads(written_json)

        assert isinstance(data, dict)
        assert isinstance(data["requirements"], list)
        assert len(data["requirements"]) == 1
        assert data["document_info"]["id"] == "gemIGTestProjekt"
        assert data["document_info"]["title"] == "Test Project IG"
        assert data["document_info"]["link"] == "https://www.example.com/1.0.0"
        assert data["document_info"]["version"] == "1.0.0"
        assert data["document_info"]["date"] == "1757635200"
        assert data["document_info"]["status"] == "released"
        assert data["document_info"]["classification"] == "public"

        assert data["requirements"][0]["key"] == "REQ-1"
        assert data["requirements"][0]["text"] == "This must be exported"
        assert data["requirements"][0]["title"] == "Exported requirement"
        assert data["requirements"][0]["version"] == 0
        assert data["requirements"][0]["status"] == "ACTIVE"
        assert data["requirements"][0]["conformance"] == "SHALL"
        assert data["requirements"][0]["link"] == "https://www.example.com/1.0.0/file.html#REQ-1"
        assert data["requirements"][0]["characteristics"] == [{"product_type": "ProductTypeB", "test_procedure":["TP-456"]}]


def test_polarion_export_raise_mapping_error(tmp_path, mock_config, mock_ig_config):
    req = Requirement(
        key="REQ-1",
        title="Exported requirement",
        actor="WRONG",
        version=0,
        conformance="SHALL",
        status="ACTIVE",
        source="file.md",
        test_procedures={"WRONG":["AN01"]}
    )
    fake_actor_map   = {"ACTOR": "ProductTypeB"}
    fake_testproc_map = {"AN01": "TP-456"}

    release = Release(name="Test Project", version="1.0.0")
    release.requirements = [req]
    exporter = PolarionExporter(config=mock_config, ig_config=mock_ig_config)

    with patch.object(exporter.release_manager, "load", return_value=release), \
         patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open()) as mocked_file, \
         patch("igtools.specifications.exporter.convert_to_link", return_value="file.html"), \
         patch("igtools.polarion.polarion.load_polarion_mappings", return_value=(fake_actor_map, fake_testproc_map)):

        with pytest.raises(PolarionExportError):
            exporter.export(str(tmp_path))


def test_polarion_export_skips_deleted_requirements(tmp_path, mock_config, mock_ig_config):
    req = Requirement(
        key="REQ-1",
        title="Exported requirement",
        actor="ACTOR",
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

        assert isinstance(data, dict)
        assert isinstance(data["requirements"], list)
        assert len(data["requirements"]) == 1
        assert data["document_info"]["id"] == "gemIGTestProjekt"
        assert data["document_info"]["title"] == "Test Project IG"
        assert data["document_info"]["link"] == "https://www.example.com/1.0.0"
        assert data["document_info"]["version"] == "1.0.0"
        assert data["document_info"]["date"] == "1757635200"
        assert data["document_info"]["status"] == "released"
        assert data["document_info"]["classification"] == "public"

        assert data["requirements"][0]["key"] == "REQ-1"
        assert data["requirements"][0]["text"] == "This must be exported"
        assert data["requirements"][0]["title"] == "Exported requirement"
        assert data["requirements"][0]["version"] == 1
        assert data["requirements"][0]["status"] == "RETIRED"
        assert data["requirements"][0]["conformance"] == "SHALL"
        assert data["requirements"][0]["link"] == "https://www.example.com/1.0.0/file.html#REQ-1-01"
        assert data["requirements"][0]["characteristics"] == []


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

    expected_data = {
        "document_info": {
            "id": "gemIGTestProjekt",
            "title": "Test Project IG",
            "link": "https://www.example.com/1.0.0",
            "version": "1.0.0",
            "date": "1757635200",
            "status": "released",
            "classification": "public"
        },
        "requirements": [
            {
                "key": "REQ-100",
                "title": "Complete Export",
                "characteristics": [],
                "version": 3,
                "status": "RETIRED",
                "link": "https://www.example.com/1.0.0/requirement.html#REQ-100-03",
                "text": "Detailed requirement text.",
                "conformance": "MAY"
            }
        ]
    }

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


def test_returns_int_for_supported_types():
    assert isinstance(convert_polarion_date_export(date(2025, 10, 22)), int)
    assert isinstance(convert_polarion_date_export(datetime(2025, 10, 22, 0, 0)), int)
    assert isinstance(convert_polarion_date_export("2025-10-22"), int)


def test_naive_inputs_yield_same_timestamp():
    """
    A date, a naive datetime, and an ISO date string representing the same calendar day
    should all result in identical Unix timestamps.
    """
    d = date(2025, 10, 22)
    dt_naive = datetime(2025, 10, 22, 0, 0, 0)
    s = "2025-10-22"

    ts_date = convert_polarion_date_export(d)
    ts_dt   = convert_polarion_date_export(dt_naive)
    ts_str  = convert_polarion_date_export(s)

    assert ts_date == ts_dt == ts_str


def test_timezone_aware_datetime_is_converted_to_utc_before_timestamp():
    """
    A timezone-aware datetime (e.g. 00:00 at UTC+02:00) must be normalized to UTC
    before converting to a Unix timestamp. The timestamp should represent the same
    absolute moment in time.
    """
    aware = datetime(2025, 10, 22, 0, 0, 0, tzinfo=timezone(timedelta(hours=2)))
    got = convert_polarion_date_export(aware)

    # Expected UTC instant is 2025-10-21 22:00:00Z
    expected_utc = datetime(2025, 10, 21, 22, 0, 0, tzinfo=timezone.utc)
    expected_ts = int(expected_utc.timestamp())

    assert got == expected_ts


def test_invalid_string_raises():
    """
    Invalid date strings must raise a PolarionExportDateError.
    """
    with pytest.raises(PolarionExportDateError):
        convert_polarion_date_export("22-10-2025")


def test_unsupported_type_raises():
    """
    Unsupported input types (e.g., integers) must raise a PolarionExportDateError.
    """
    with pytest.raises(PolarionExportDateError):
        convert_polarion_date_export(20251022)


def test_epoch_matches_utc_midnight_when_using_iso_string():
    """
    If the implementation is UTC-safe (recommended), the ISO date string 'YYYY-MM-DD'
    should correspond to midnight UTC of that day.

    This test compares the output against calendar.timegm(), which always uses UTC.
    Note: If the implementation uses time.mktime() (local time), this test may fail
    on systems with non-UTC timezones.
    """
    s = "2025-10-22"
    ts = convert_polarion_date_export(s)

    # UTC midnight for that day:
    expected = calendar.timegm((2025, 10, 22, 0, 0, 0, 0, 1, -1))
    assert ts == expected