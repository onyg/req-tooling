import pytest

from igtools.utils import utils

class Dummy:
    @utils.validate_type(str)
    def set_value(self, value):
        return value


def test_validate_type_correct():
    d = Dummy()
    assert d.set_value("test") == "test"


def test_validate_type_incorrect():
    d = Dummy()
    with pytest.raises(TypeError, match="Expected a value of type str"):
        d.set_value(123)


@pytest.mark.parametrize("input_value, expected", [
    ("hello", "hello"),
    (["a", "b", "c"], "a, b, c"),
    (123, "123"),
])
def test_to_str(input_value, expected):
    assert utils.to_str(input_value) == expected


@pytest.mark.parametrize("input_value, expected", [
    (["a", "b", "c"], ["a", "b", "c"]),
    ("a, b, c", ["a", "b", "c"]),
    (123, [123]),
])
def test_to_list(input_value, expected):
    assert utils.to_list(input_value) == expected


def test_distinct_list_correct():
    input_list = ["a", "b", "a", "c"]
    output_list = utils.distinct_list(input_list)
    assert sorted(output_list) == ["a", "b", "c"]


def test_distinct_list_incorrect_type():
    with pytest.raises(TypeError, match="Expected a value of type list"):
        utils.distinct_list("a,b,c")


def test_clean_list():
    input_list = ["a", "", "b", " ", "c", "a"]
    output_list = utils.clean_list(input_list)
    assert sorted(output_list) == ["a", "b", "c"]


def test_clean_list_incorrect_type():
    with pytest.raises(TypeError, match="Expected a value of type list"):
        utils.clean_list("a, b, c")


@pytest.mark.parametrize("source, key, version, expected", [
    ("folder/file.md", None, None, "file.html"),
    ("folder/file.xml", "section1", None, "file.html#section1"),
    ("folder/file.md", "section1", 2, "file.html#section1-2"),
    ("folder/file.md", None, 2, "file.html"),
])
def test_convert_to_link(source, key, version, expected):
    assert utils.convert_to_link(source, key=key, version=version) == expected


def test_normalize_removes_spaces_and_tabs():
    assert utils.normalize("  This is   a test\t") == "thisisatest"


def test_normalize_removes_linebreaks():
    assert utils.normalize("This\nis\na\ntest") == "thisisatest"


def test_normalize_mixed_whitespace():
    assert utils.normalize(" \nThis\t is  \na \ttest ") == "thisisatest"


def test_normalize_is_case_insensitive():
    assert utils.normalize("This Is A TEST") == "thisisatest"

@pytest.mark.parametrize("input_value, expected", [
    ("This <b>is</b> A TEST", "thisisatest"),
    ("<table><tr><td>This</td></tr><tr><td><b>is</b> A TEST</td></tr></table>", "thisisatest"),
])
def test_normalize_with_no_html_tags(input_value, expected):
    assert utils.normalize(input_value) == expected


def test_normalize_empty_string():
    assert utils.normalize("") == ""


def test_normalize_only_whitespace():
    assert utils.normalize(" \t\n  ") == ""


@pytest.mark.parametrize("input_value, expected", [
    ("This is \n a \r test.", "This is \n a \n test."),
    ("This is \n\r a \r test.", "This is \n\n a \n test."),
])
def test_clean_text_general_newline(input_value, expected):
    assert utils.clean_text(input_value) == expected


@pytest.mark.parametrize("input_value, expected", [
    ("  This is   a test\t", "This is a test\t"),
    ("  This is  \n    a test.  ", "This is \n a test."),
])
def test_clean_text_removes_redundant_spaces(input_value, expected):
    assert utils.clean_text(input_value) == expected
