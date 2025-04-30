import os
import pytest
import tarfile
import io
from unittest.mock import patch, MagicMock, mock_open, PropertyMock

from igtools.extractor.fhir import FHIRPackageExtractor, FilePathNotExists, DownloadException, FileFormatException

@pytest.fixture
def extractor():
    return FHIRPackageExtractor(config={})


def test_prepare_output_folder_creates_directory(tmp_path, extractor):
    output_dir = tmp_path / "output"

    # Should create directory even if it doesn't exist
    extractor._prepare_output_folder(str(output_dir))
    assert output_dir.exists()


def test_prepare_output_folder_removes_existing_directory(tmp_path, extractor):
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "dummy.txt").write_text("dummy")

    extractor._prepare_output_folder(str(output_dir))
    assert output_dir.exists()
    assert not any(output_dir.iterdir())  # Directory should be empty


def test_generate_possible_filenames(extractor):
    filenames = extractor._generate_possible_filenames("Patient", "123")
    assert "Patient-123.json" in filenames
    assert "123.Patient.json" in filenames
    assert "Patient-123.xml" in filenames
    assert "123.Patient.xml" in filenames
    assert os.path.join('Patient', '123.json') in filenames
    assert os.path.join('Patient', '123.xml') in filenames
    assert os.path.join('examples', 'Patient-123.json') in filenames
    assert os.path.join('examples', '123.Patient.json') in filenames
    assert os.path.join('examples', 'Patient-123.xml') in filenames
    assert os.path.join('examples', '123.Patient.xml') in filenames


def test_copy_resource(tmp_path, extractor):
    src_file = tmp_path / "resource.json"
    src_file.write_text('{"resourceType": "Patient"}')
    target_dir = tmp_path / "target"
    target_dir.mkdir()

    with patch("igtools.extractor.fhir.cli.print_command") as mock_print:
        extractor._copy_resource(str(src_file), str(target_dir))

        copied_file = target_dir / src_file.name
        assert copied_file.exists()
        mock_print.assert_called_once()


def test_process_resource_found(tmp_path, extractor):
    package_folder = tmp_path / "package"
    package_folder.mkdir()
    resource_file = package_folder / "Patient-123.json"
    resource_file.write_text('{"resourceType": "Patient"}')
    output_folder = tmp_path / "output"
    output_folder.mkdir()

    with patch("igtools.extractor.fhir.cli.print_command") as mock_print:
        extractor._process_resource(str(package_folder), "Patient/123", str(output_folder))
        assert (output_folder / "Patient-123.json").exists()


def test_process_resource_not_found(tmp_path, extractor):
    package_folder = tmp_path / "package"
    package_folder.mkdir()
    output_folder = tmp_path / "output"
    output_folder.mkdir()

    with patch("igtools.extractor.fhir.cli.print_command") as mock_print:
        extractor._process_resource(str(package_folder), "Patient/999", str(output_folder))
        mock_print.assert_called_once()


def test_ensure_package_downloaded_finds_existing_package(tmp_path, extractor):
    existing_package = tmp_path / "mypackage#1.0.0" / "package"
    existing_package.mkdir(parents=True)

    with patch.object(FHIRPackageExtractor, "fhir_package_folders", new_callable=PropertyMock) as mock_folders:
        mock_folders.return_value = [str(tmp_path)]
        path = extractor._ensure_package_downloaded("mypackage", "1.0.0")
        assert path.endswith("mypackage#1.0.0/package")


def test_ensure_package_downloaded_downloads_and_extracts(tmp_path, extractor):
    package_content = io.BytesIO()
    with tarfile.open(fileobj=package_content, mode='w:gz') as tar:
        info = tarfile.TarInfo(name="package/resource.json")
        content = b'{"resourceType": "Patient"}'
        info.size = len(content)
        tar.addfile(tarinfo=info, fileobj=io.BytesIO(content))

    package_content.seek(0)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raw = package_content

    with patch("requests.get", return_value=mock_response), \
        patch("os.makedirs"), \
        patch("builtins.open", new_callable=mock_open), \
        patch("igtools.extractor.fhir.tarfile.open") as mock_tar_open, \
        patch("os.remove"):

        mock_tar = MagicMock()
        mock_tar.extractall = MagicMock()
        mock_tar_open.return_value.__enter__.return_value = mock_tar

        extractor.download_folder = str(tmp_path)
        extractor._ensure_package_downloaded("mypackage", "1.0.0")

        mock_tar.extractall.assert_called_once()


def test_ensure_package_downloaded_bad_download(tmp_path, extractor):
    mock_response = MagicMock()
    mock_response.status_code = 404

    with patch("requests.get", return_value=mock_response):
        with pytest.raises(DownloadException):
            extractor._ensure_package_downloaded("nonexistingpackage", "1.0.0")


def test_process_missing_config_file(extractor):
    with pytest.raises(FilePathNotExists):
        extractor.process(config_filename="non_existing_file.yaml")
