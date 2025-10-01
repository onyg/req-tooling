import os
import pytest
from datetime import datetime
from bs4 import BeautifulSoup
from unittest.mock import MagicMock, patch, mock_open

from igtools.config import CONFIG_DEFAULT_DIR
from igtools.specifications.manager import Processor
from igtools.errors import NoReleaseVersionSetException, ReleaseNotFoundException, DuplicateRequirementIDException, FinalReleaseException
from igtools.specifications.data import Requirement, Release, ReleaseState


@pytest.fixture
def mock_config():
    return MagicMock(
        current="1.0.0",
        final=None,
        directory=CONFIG_DEFAULT_DIR,
        prefix="REQ",
        separator="-",
        scope="PYT",
        add_release=MagicMock(),
        save=MagicMock()
    )


@pytest.fixture
def processor(mock_config):
    return Processor(mock_config)


def test_is_process_file(processor):
    assert processor.is_process_file("test.html") is True
    assert processor.is_process_file("note.md") is True
    assert processor.is_process_file("image.png") is False


def test_check_raises_no_version(processor):
    processor.config.current = None
    with pytest.raises(NoReleaseVersionSetException):
        processor.check()


def test_check_raises_release_not_found(processor):
    with patch("os.path.exists", return_value=False):
        with pytest.raises(ReleaseNotFoundException):
            processor.check()


def test_validate_requirements_duplicate_key(processor):
    r1 = Requirement(key="REQ-TST00001A00", source="a.html")
    r2 = Requirement(key="REQ-TST00001A00", source="b.html")
    processor.release_manager.load = MagicMock(return_value=Release())
    processor.release_manager.load.return_value.archive = [r1]
    processor.release_manager.load.return_value.requirements = [r2]

    with pytest.raises(DuplicateRequirementIDException):
        processor._validate_requirements()


def test_validate_input_files_duplicate_key(tmp_path, processor):
    html = '<requirement key="REQ-TST00001A00"></requirement>'
    file_path = tmp_path / "test.html"
    file_path.write_text(html)

    processor.input_path = tmp_path
    processor.release_manager.load = MagicMock(return_value=Release())
    processor.release_manager.load.return_value.archive = [Requirement(key="REQ-TST00001A00")]

    with pytest.raises(DuplicateRequirementIDException):
        processor._validate_input_files()


def test_update_or_create_requirement_creates_new(processor):
    soup = BeautifulSoup('<requirement title="Title" actor="EPA-Medication-Service">Text</requirement>', 'html.parser')
    soup_tag = soup.requirement

    with patch("igtools.specifications.manager.id.generate_id", return_value="REQ-TST00001A00"), \
         patch("igtools.specifications.manager.id.add_id"):

        req = processor._update_or_create_requirement(soup_tag, {}, "file.html", text="Text")
        assert req.key == "REQ-TST00001A00"
        assert req.version == 0
        assert req.title == "Title"
        assert req.actor == ["EPA-Medication-Service"]
        assert req.text == "Text"
        assert req.source == "file.html"


def test_detect_removed_requirement_marks_deleted(processor):
    existing = {"REQ-TST00001A00": Requirement(key="REQ-TST00001A00")}
    current = []

    processor._detect_removed_requirements(current, existing)
    assert len(current) == 1
    assert current[0].is_deleted
    assert current[0].deleted is not None


def test_process_file_parses_and_updates(tmp_path, processor):
    file_path = tmp_path / "test.html"
    file_path.write_text('<requirement title="X" actor="EPA-PS">Text</requirement>')

    with patch.object(processor, "_update_or_create_requirement") as mock_update:
        req = Requirement(key="REQ-TST00001A00")
        mock_update.return_value = req
        result = processor._process_file(str(file_path), {})
        assert result == [req]

def test_process_executes_all(tmp_path, processor):
    html = '<requirement title="X" actor="EPA-PS">Text</requirement>'
    file_path = tmp_path / "req.html"
    file_path.write_text(html)

    old = Requirement(key="OLD-1")
    release = Release(name="R", version="1.0.0")
    release.requirements = [old]

    processor.input_path = tmp_path

    with patch.object(processor.release_manager, "check_final", return_value=False), \
         patch.object(processor.release_manager, "load", return_value=release), \
         patch.object(processor.release_manager, "save"), \
         patch("igtools.specifications.manager.id.generate_id", return_value="REQ-NEW"), \
         patch("igtools.specifications.manager.id.add_id"), \
         patch("os.path.exists", return_value=True):

        processor.process()
        assert len(release.requirements) == 2
        keys = {r.key for r in release.requirements}
        assert "OLD-1" in keys
        assert "REQ-NEW" in keys



def test_process_file_writes_expected_html_exactly(tmp_path, processor):
    original_html = """
    <html>
        <body>
            <requirement title="Test" actor="EPA-PS" conformance="SHALL">
                Some inner text
                <table style="width: 100%">
                    <thead>
                    <tr>
                        <th>Code</th>
                        <th>Desc</th>
                        <th>Error Code</th>
                    </tr>
                    </thead>
                    <tbody>
                    <tr>
                        <td>423</td>
                        <td>Service is locked</td>
                        <td>locked</td>
                    </tr>
                    </tbody>
                </table>
            </requirement>
            <br/><br/>
            <ul>
                <li>ONE</li>
                <li>TWO</li>
                <li>THREE</li>
            </ul>
            <br/><br/>
            <a href="https://example.com/page?user=42&token=abc">Information</a>
        </body>
    </html>
    """

    expected_html = """
    <html>
        <body>
            <requirement actor="EPA-PS" conformance="SHALL" key="REQ-123" title="Test" version="1">
                Some inner text
                <table style="width: 100%">
                    <thead>
                    <tr>
                        <th>Code</th>
                        <th>Desc</th>
                        <th>Error Code</th>
                    </tr>
                    </thead>
                    <tbody>
                    <tr>
                        <td>423</td>
                        <td>Service is locked</td>
                        <td>locked</td>
                    </tr>
                    </tbody>
                </table>
            </requirement>
            <br/><br/>
            <ul>
                <li>ONE</li>
                <li>TWO</li>
                <li>THREE</li>
            </ul>
            <br/><br/>
            <a href="https://example.com/page?user=42&token=abc">Information</a>
        </body>
    </html>
    """

    file_path = tmp_path / "req.html"
    file_path.write_text(original_html)

    fake_req = Requirement(key="REQ-123", version=1)

    def update_mock(soup_req, existing_map, file_path, text):
        soup_req['key'] = "REQ-123"
        soup_req['version'] = "1"
        return fake_req

    with patch("builtins.open", mock_open(read_data=original_html)) as mocked_open, \
         patch.object(processor, "_update_or_create_requirement", side_effect=update_mock):

        processor._process_file(str(file_path), {})

        handle = mocked_open()
        handle.write.assert_called_once()
        written_html = handle.write.call_args[0][0]

        assert written_html == expected_html


def test_process_file_multiple_requirements(tmp_path, processor):
    original_html = """
    <html>
        <body>
            <requirement title="A" actor="ACTOR-A" conformance="SHALL">
                Text A
            </requirement>
            <p>Zwischentext</p>
            <requirement title="B" actor="ACTOR-B" conformance="SHALL">
                Text B
            </requirement>
        </body>
    </html>
    """

    expected_html = """
    <html>
        <body>
            <requirement actor="ACTOR-A" conformance="SHALL" key="REQ-1" title="A" version="1">
                Text A
            </requirement>
            <p>Zwischentext</p>
            <requirement actor="ACTOR-B" conformance="SHALL" key="REQ-2" title="B" version="1">
                Text B
            </requirement>
        </body>
    </html>
    """

    file_path = tmp_path / "req.html"
    file_path.write_text(original_html)

    keys = iter(["REQ-1", "REQ-2"])

    def update_mock(soup_req, existing_map, file_path, text):
        key = next(keys)
        soup_req["key"] = key
        soup_req["version"] = "1"
        return Requirement(key=key, version=1)

    with patch("builtins.open", mock_open(read_data=original_html)) as mocked_open, \
         patch.object(processor, "_update_or_create_requirement", side_effect=update_mock):

        processor._process_file(str(file_path), {})

        handle = mocked_open()
        handle.write.assert_called_once()
        written_html = handle.write.call_args[0][0]

        assert written_html == expected_html


def test_process_file_updates_existing_requirement_on_text_change(tmp_path, processor):
    original_html = """
    <html>
        <body>
            <requirement actor="EPA-PS" conformance="SHALL" key="REQ-0023" title="Test" version="1">
                New text content
            </requirement>
            <p>Some more HTML</p>
        </body>
    </html>
    """

    expected_html = """
    <html>
        <body>
            <requirement actor="EPA-PS" conformance="SHALL" key="REQ-0023" title="Test" version="2">
                New text content
            </requirement>
            <p>Some more HTML</p>
        </body>
    </html>
    """

    file_path = tmp_path / "req.html"
    file_path.write_text(original_html)

    # existing requirement with old text
    existing_req = Requirement(
        key="REQ-0023",
        title="Test",
        actor=["EPA-PS"],
        conformance="SHALL",
        text="Old text content",
        version=1,
        process=ReleaseState.STABLE.value
    )

    existing_map = {"REQ-0023": existing_req}


    with patch("builtins.open", mock_open(read_data=original_html)) as mocked_open:

        processor._process_file(str(file_path), existing_map)

        handle = mocked_open()
        handle.write.assert_called_once()
        written_html = handle.write.call_args[0][0]
        
        assert written_html == expected_html


def test_process_file_preserves_requirement_inner_text_exactly(tmp_path, processor):
    original_html = '''
    <html>
        <body>
            <requirement actor="EPA-PS" conformance="SHALL" title="Test" actor="USER">
                <actor name="EPA-PS">
                    <testProcedure id="AN04"/>
                </actor>
                More information: <a href="https://example.com/page?user=42&token=abc">Information</a>.
            </requirement>
        </body>
    </html>
    '''

    expected_text = 'More information: <a href="https://example.com/page?user=42&token=abc">Information</a>.'
    file_path = tmp_path / "req.html"
    file_path.write_text(original_html)

    # Wrap the real method so it's still called
    with patch.object(processor, "create_new_requirement", wraps=processor.create_new_requirement) as wrapped_create:
        requirements = processor._process_file(str(file_path), {})

        # Ensure result is correct
        assert len(requirements) == 1
        assert requirements[0].text.strip() == expected_text

        # Ensure create_new_requirement was really called (not mocked)
        wrapped_create.assert_called_once()


def test_update_existing_requirement_no_change(processor):
    req = Requirement(key="REQ-001", text="This is a text.", title="Title", actor=["ACTOR"], conformance="SHALL", version=1, source="file.md", process=ReleaseState.STABLE.value, test_procedures={"ACTOR":[]})
    result = processor.update_existing_requirement(req, text="This is a text.", title="Title", actor=["ACTOR"], file_path="file.md", conformance="SHALL", test_procedures={"ACTOR":[]})
    assert result.version == 1
    assert result.is_stable


def test_update_existing_requirement_only_formatting_change(processor):
    req = Requirement(key="REQ-001", text="This is a text.", title="Titel", actor="ACTOR", conformance="SHALL", version=1, source="file.md", process=ReleaseState.STABLE.value)
    # Text with extra whitespace and line breaks
    new_text = "   This is  \n a   text.   "
    expected_text = "This is \n a text."
    result = processor.update_existing_requirement(req, text=new_text, title="Titel", actor="ACTOR", file_path="file.md", conformance="SHALL", test_procedures={})
    assert result.text == expected_text
    assert result.is_stable
    assert result.version == 1


def test_update_existing_requirement_content_changed(processor):
    req = Requirement(key="REQ-001", text="This is a text.", title="Titel", actor="ACTOR", conformance="SHALL", version=1, source="file.md", process=ReleaseState.STABLE.value)
    new_text = "This is a different text."
    result = processor.update_existing_requirement(req, text=new_text, title="Titel", actor="ACTOR", file_path="file.html", conformance="SHALL", test_procedures={"ACTOR":[]})
    assert result.is_modified
    assert result.version == 2
    assert result.text == new_text