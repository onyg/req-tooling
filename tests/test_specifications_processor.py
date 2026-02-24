import os
import pytest
from datetime import datetime
from bs4 import BeautifulSoup
from unittest.mock import MagicMock, patch, mock_open

from igtools.config import CONFIG_DEFAULT_DIR
from igtools.specifications.processor import Processor, FileProcessor
from igtools.utils.id import SequentialIdGenerator, RandomIdGenerator
from igtools.errors import (
    NoReleaseVersionSetException,
    ReleaseNotFoundException,
    DuplicateRequirementIDException,
    InvalidTestProcedureIDException,
    FinalReleaseException,
)
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
        key_mode="random",
        current_req_number=0,
        add_release=MagicMock(),
        save=MagicMock()
    )


@pytest.fixture
def processor(mock_config):
    p = Processor(mock_config)
    p.key_generator = RandomIdGenerator(config=p.config) 
    return p


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


def test_validate_requirements_with_duplicate_key_in_files(tmp_path, processor):
    processor.release_manager.load = MagicMock(return_value=Release())
    processor.release_manager.load.return_value.requirements = []

    content = """
    <html>
        <body>
            <requirement title="Test" key="REQ-TST00001A03" conformance="SHALL">
                <actor name="Service"></actor>
                Some inner text
            </requirement>
            <br/><br/>
            <requirement title="Test2" key="REQ-TST00001A03" conformance="SHALL">
                <actor name="Service"></actor>
                Some inner text2
            </requirement>
        </body>
    </html>
    """

    file_path = tmp_path / "test.html"
    file_path.write_text(content)

    processor.input_path = tmp_path

    with patch("builtins.open", mock_open(read_data=content)) as mocked_open, \
         patch("os.path.exists", return_value=True):

        with pytest.raises(DuplicateRequirementIDException):
            processor.check()


def test_validate_requirements_with_duplicate_empty_keys(tmp_path, processor):
    processor.release_manager.load = MagicMock(return_value=Release())
    processor.release_manager.load.return_value.requirements = []

    content = """
    <html>
        <body>
            <requirement title="Test" key="" conformance="SHALL">
                <actor name="Service"></actor>
                Some inner text
            </requirement>
            <br/><br/>
            <requirement title="Test2" key="" conformance="SHALL">
                <actor name="Service"></actor>
                Some inner text2
            </requirement>
        </body>
    </html>
    """

    file_path = tmp_path / "test.html"
    file_path.write_text(content)
    processor.input_path = tmp_path

    with patch("builtins.open", mock_open(read_data=content)) as mocked_open, \
         patch("os.path.exists", return_value=True):

        try:
            processor.check()
        except DuplicateRequirementIDException as e:
            pytest.fail(f"DuplicateRequirementIDException was raised unexpectedly: {e}")


def test_validate_input_files_duplicate_key(tmp_path, processor):
    html = '<requirement key="REQ-TST00001A00"></requirement>'
    file_path = tmp_path / "test.html"
    file_path.write_text(html)

    processor.input_path = tmp_path
    processor.release_manager.load = MagicMock(return_value=Release())
    processor.release_manager.load.return_value.archive = [Requirement(key="REQ-TST00001A00")]

    with pytest.raises(DuplicateRequirementIDException):
        processor._validate_input_files()


def test_validate_input_files_raises_for_unknown_testprocedure_id(tmp_path, processor):
    html = """
    <requirement key="REQ-TST00001A00" conformance="SHALL">
        <actor name="EPA-PS">
            <testProcedure id="UnknownProcedure"/>
        </actor>
        Text
    </requirement>
    """
    file_path = tmp_path / "test.html"
    file_path.write_text(html)

    processor.input_path = tmp_path
    processor.release_manager.load = MagicMock(return_value=Release())
    processor.release_manager.load.return_value.archive = []

    with patch("igtools.polarion.polarion.load_polarion_mappings", return_value=({}, {"Produkttest": {"id": "testProcedurePT03"}})):
        with pytest.raises(InvalidTestProcedureIDException) as exc_info:
            processor._validate_input_files()

    assert "Unknown testProcedure id 'UnknownProcedure'" in str(exc_info.value)


def test_update_or_create_requirement_creates_new(processor):
    soup = BeautifulSoup('<requirement title="Title" actor="EPA-Medication-Service">Text</requirement>', 'html.parser')
    soup_tag = soup.requirement

    with patch("igtools.specifications.processor.id.generate_id", return_value="REQ-TST00001A00"), \
         patch("igtools.specifications.processor.id.add_id"):

        fp = FileProcessor(processor=processor, file_path="file.html", existing_map={})
        req = fp._update_or_create_requirement(soup_req=soup_tag, text="Text")
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

    fp = FileProcessor(processor=processor, file_path=str(file_path), existing_map={})
    with patch.object(fp, "_update_or_create_requirement") as mock_update:
        req = Requirement(key="REQ-TST00001A00")
        mock_update.return_value = req
        result = fp.process()
        assert result == [req]


def test_process_file_fills_testprocedure_values_from_polarion_mapping(tmp_path, processor):
    original_html = """
    <requirement title="X" actor="EPA-PS" conformance="SHALL">
        <actor name="EPA-PS">
            <testProcedure id="Produkttest"/>
            <testProcedure id="Produktgutachten">Foo</testProcedure>
        </actor>
        Text
    </requirement>
    """
    file_path = tmp_path / "req.html"
    file_path.write_text(original_html)

    fp = FileProcessor(processor=processor, file_path=str(file_path), existing_map={})

    with patch.object(fp, "_update_or_create_requirement", return_value=Requirement(key="REQ-1")), \
         patch("igtools.polarion.polarion.load_polarion_mappings", return_value=(
             {},
             {
                 "Produkttest": {"id": "testProcedurePT03", "name": "funkt. Eignung: Test Produkt/FA"},
                 "Produktgutachten": {"id": "testProcedurePT27", "name": "Sich.techn. Eignung: Produktgutachten"},
             },
         )):
        fp.process()

    written_html = file_path.read_text()
    assert '<testProcedure id="Produkttest">funkt. Eignung: Test Produkt/FA</testProcedure>' in written_html
    assert '<testProcedure id="Produktgutachten">Sich.techn. Eignung: Produktgutachten</testProcedure>' in written_html


def test_process_files_assigns_sequential_ids(tmp_path, mock_config):
    mock_config.scope = "PYT"
    mock_config.key_mode = "sequential"
    mock_config.current_req_number = 1  # Start from 1, should create REQ-PYT2, REQ-PYT3
    processor = Processor(mock_config, input=tmp_path)

    html = """
    <html>
        <body>
            <requirement title="A" actor="ACTOR-A">Text A</requirement>
            <requirement title="B" actor="ACTOR-B">Text B</requirement>
        </body>
    </html>
    """
    file_path = tmp_path / "req.html"
    file_path.write_text(html)

    existing_map = {"REQ-PYT1": Requirement(key="REQ-PYT1")}
    processor.key_generator = SequentialIdGenerator(config=mock_config, existing_keys=existing_map.keys())

    with patch("igtools.specifications.processor.id.generate_id", side_effect=AssertionError("should use sequential id generator")), \
         patch("igtools.specifications.processor.id.add_id", return_value=True):
        requirements = processor._process_files(existing_map=existing_map, dry_run=True)

    assert len(requirements) == 2
    assert {req.key for req in requirements} == {"REQ-PYT2", "REQ-PYT3"}


def test_processor_updates_current_req_number(tmp_path, mock_config):
    mock_config.key_mode = "sequential"
    mock_config.current_req_number = 5

    html = """
    <html>
        <body>
            <requirement title="A" actor="ACTOR-A">Text A</requirement>
            <requirement title="B" actor="ACTOR-B">Text B</requirement>
        </body>
    </html>
    """
    file_path = tmp_path / "req.html"
    file_path.write_text(html)

    release = Release(name="R", version="1.0.0")
    release.requirements = []
    release.archive = []

    processor = Processor(mock_config, input=tmp_path)
    processor.release_manager = MagicMock()
    processor.release_manager.load.return_value = release
    processor.release_manager.save = MagicMock()
    processor.release_manager.is_current_release_frozen.return_value = False

    processor.check = MagicMock(return_value=None)

    with patch("igtools.specifications.processor.id.add_id", return_value=True):
        processor.process()

    assert mock_config.current_req_number == 7
    assert len(release.requirements) == 2
    keys = {req.key for req in release.requirements}
    assert keys == {"REQ-PYT6", "REQ-PYT7"}


def test_process_executes_all(tmp_path, processor):
    html = '<requirement title="X" actor="EPA-PS">Text</requirement>'
    file_path = tmp_path / "req.html"
    file_path.write_text(html)

    old = Requirement(key="OLD-1")
    release = Release(name="R", version="1.0.0")
    release.requirements = [old]

    processor.input_path = tmp_path

    with patch.object(processor.release_manager, "raise_if_frozen", return_value=False), \
         patch.object(processor.release_manager, "load", return_value=release), \
         patch.object(processor.release_manager, "save"), \
         patch("igtools.specifications.processor.id.generate_id", return_value="REQ-NEW"), \
         patch("igtools.specifications.processor.id.add_id"), \
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

    fp = FileProcessor(processor=processor, file_path=str(file_path), existing_map={})

    def update_mock(soup_req, text=None):
        soup_req['key'] = "REQ-123"
        soup_req['version'] = "1"
        return fake_req

    with patch("builtins.open", mock_open(read_data=original_html)) as mocked_open, \
         patch.object(fp, "_update_or_create_requirement", side_effect=update_mock):

        fp.process()

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

    fp = FileProcessor(processor=processor, file_path=str(file_path), existing_map={})

    def update_mock(soup_req, text):
        key = next(keys)
        soup_req["key"] = key
        soup_req["version"] = "1"
        return Requirement(key=key, version=1)

    with patch("builtins.open", mock_open(read_data=original_html)) as mocked_open, \
         patch.object(fp, "_update_or_create_requirement", side_effect=update_mock):

        fp.process()

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

    fp = FileProcessor(processor=processor, file_path=str(file_path), existing_map=existing_map)

    with patch("builtins.open", mock_open(read_data=original_html)) as mocked_open:

        fp.process()

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
                    <testProcedure id="AN05"/>
                </actor>
                More information: <a href="https://example.com/page?user=42&token=abc">Information</a>.
            </requirement>
        </body>
    </html>
    '''

    expected_text = 'More information: <a href="https://example.com/page?user=42&token=abc">Information</a>.'
    file_path = tmp_path / "req.html"
    file_path.write_text(original_html)

    fp = FileProcessor(processor=processor, file_path=str(file_path), existing_map={})

    # Wrap the real method so it's still called
    with patch.object(fp, "create_new_requirement", wraps=fp.create_new_requirement) as wrapped_create:
        requirements = fp.process()

        # Ensure result is correct
        assert len(requirements) == 1
        assert requirements[0].text.strip() == expected_text

        # Ensure create_new_requirement was really called (not mocked)
        wrapped_create.assert_called_once()


def test_update_existing_requirement_no_change(processor):
    file_path = "file.md"
    req = Requirement(key="REQ-001", text="This is a text.", title="Title", actor=["ACTOR"], conformance="SHALL", version=1, source=file_path, process=ReleaseState.STABLE.value, test_procedures={"ACTOR":[]})
    fp = FileProcessor(processor=processor, file_path=str(file_path), existing_map={})
    result = fp.update_existing_requirement(req, text="This is a text.", title="Title", actor=["ACTOR"], conformance="SHALL", test_procedures={"ACTOR":[]})

    assert result.version == 1
    assert result.is_stable


def test_update_existing_requirement_only_formatting_change(processor):
    file_path = "file.md"
    req = Requirement(key="REQ-001", text="This is a text.", title="Titel", actor="ACTOR", conformance="SHALL", version=1, source="file.md", process=ReleaseState.STABLE.value)
    # Text with extra whitespace and line breaks
    new_text = "   This is  \n a   text.   "
    expected_text = "This is \n a text."
    fp = FileProcessor(processor=processor, file_path=str(file_path), existing_map={})
    result = fp.update_existing_requirement(req, text=new_text, title="Titel", actor="ACTOR", conformance="SHALL", test_procedures={})

    assert result.text == expected_text
    assert result.is_stable
    assert result.version == 1


def test_update_existing_requirement_content_changed(processor):
    file_path = "file.md"
    req = Requirement(key="REQ-001", text="This is a text.", title="Titel", actor="ACTOR", conformance="SHALL", version=1, source="file.md", process=ReleaseState.STABLE.value)
    new_text = "This is a different text."
    fp = FileProcessor(processor=processor, file_path=str(file_path), existing_map={})
    result = fp.update_existing_requirement(req, text=new_text, title="Titel", actor="ACTOR", conformance="SHALL", test_procedures={})

    assert result.is_modified
    assert result.version == 2
    assert result.text == new_text


def test_update_existing_requirement_only_actors(processor):
    file_path = "file.md"
    req = Requirement(key="REQ-001", text="This is a text.", title="Titel", actor="ACTOR", conformance="SHALL", version=1, source="file.md", process=ReleaseState.STABLE.value)
    new_text = "This is a text."
    fp = FileProcessor(processor=processor, file_path=str(file_path), existing_map={})
    result = fp.update_existing_requirement(req, text=new_text, title="Titel", actor="ACTOR, ACTOR2", conformance="SHALL", test_procedures={})

    assert result.is_stable
    assert result.version == 1
    assert result.text == new_text
    assert result.actor == ["ACTOR", "ACTOR2"]


def assert_requirement_actor(tmp_path, processor, original_html, actors):
    file_path = tmp_path / "req.html"
    file_path.write_text(original_html)
    fp = FileProcessor(processor=processor, file_path=str(file_path), existing_map={})
    # Wrap the real method so it's still called
    with patch.object(fp, "create_new_requirement", wraps=fp.create_new_requirement) as wrapped_create:
        requirements = fp.process()

        # Ensure result is correct
        assert len(requirements) == 1
        assert requirements[0].actor == actors

        # Ensure create_new_requirement was really called (not mocked)
        wrapped_create.assert_called_once()


def test_process_file_preserves_requirement_one_actor(tmp_path, processor):
    original_html = '''
    <html>
        <body>
            <requirement actor="EPA-PS" conformance="SHALL" title="Test" actor="USER">
                <actor name="EPA-PS">
                    <testProcedure id="AN04"/>
                    <testProcedure id="AN05"/>
                </actor>
                More information: <a href="https://example.com/page?user=42&token=abc">Information</a>.
            </requirement>
        </body>
    </html>
    '''
    assert_requirement_actor(tmp_path=tmp_path, processor=processor, original_html=original_html, actors=["EPA-PS"])



def test_process_file_preserves_requirement_two_actor(tmp_path, processor):
    original_html = '''
    <html>
        <body>
            <requirement actor="EPA-PS" conformance="SHALL" title="Test" actor="USER">
                <actor name="EPA-PS">
                    <testProcedure id="AN04"/>
                    <testProcedure id="AN05"/>
                </actor>
                <actor name="CLIENT">
                    <testProcedure id="AN04"/>
                </actor>
                <actor name="CLIENT0">
                </actor>
                More information: <a href="https://example.com/page?user=42&token=abc">Information</a>.
            </requirement>
        </body>
    </html>
    '''
    assert_requirement_actor(tmp_path=tmp_path, processor=processor, original_html=original_html, actors=["EPA-PS", "CLIENT", "CLIENT0"])


def test_process_file_preserves_requirement_actor_test_procedure_all_active(tmp_path, processor):
    original_html = '''
    <html>
        <body>
            <requirement actor="EPA-PS" conformance="SHALL" title="Test" actor="USER">
                <actor name="EPA-PS">
                    <testProcedure id="AN04"/>
                    <testProcedure id="AN05"/>
                </actor>
                More information: <a href="https://example.com/page?user=42&token=abc">Information</a>.
            </requirement>
        </body>
    </html>
    '''
    file_path = tmp_path / "req.html"
    file_path.write_text(original_html)

    expected_test_procedures = {
        "EPA-PS": [
            "AN04",
            "AN05"
        ]
    }

    fp = FileProcessor(processor=processor, file_path=str(file_path), existing_map={})

    # Wrap the real method so it's still called
    with patch.object(fp, "create_new_requirement", wraps=fp.create_new_requirement) as wrapped_create:
        requirements = fp.process()

        # Ensure result is correct
        assert len(requirements) == 1
        assert requirements[0].test_procedures == expected_test_procedures

        # Ensure create_new_requirement was really called (not mocked)
        wrapped_create.assert_called_once()


def test_process_file_preserves_requirement_actor_test_procedure_on_inactive(tmp_path, processor):
    original_html = '''
    <html>
        <body>
            <requirement actor="EPA-PS" conformance="SHALL" title="Test" actor="USER">
                <actor name="EPA-PS">
                    <testProcedure id="AN04"/>
                    <testProcedure active="false" id="AN05"/>
                    <testProcedure active="False" id="AN05"/>
                    <testProcedure active="0" id="AN06"/>
                    <testProcedure active="True" id="AN07"/>
                    <testProcedure active="WRONG" id="AN08"/>
                </actor>
                More information: <a href="https://example.com/page?user=42&token=abc">Information</a>.
            </requirement>
        </body>
    </html>
    '''
    file_path = tmp_path / "req.html"
    file_path.write_text(original_html)

    expected_test_procedures = {
        "EPA-PS": [
            "AN04",
            "AN07"
        ]
    }

    fp = FileProcessor(processor=processor, file_path=str(file_path), existing_map={})

    # Wrap the real method so it's still called
    with patch.object(fp, "create_new_requirement", wraps=fp.create_new_requirement) as wrapped_create:
        requirements = fp.process()

        # Ensure result is correct
        assert len(requirements) == 1
        assert requirements[0].test_procedures == expected_test_procedures

        # Ensure create_new_requirement was really called (not mocked)
        wrapped_create.assert_called_once()
