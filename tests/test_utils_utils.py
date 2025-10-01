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
    ("folder/file.md", "section1", 2, "file.html#section1-02"),
    ("folder/file.md", None, 2, "file.html"),
    ("folder/file.md", "IG-REQ0001ABC", 0, "file.html#IG-REQ0001ABC"),
    ("folder/file.md", "IG-REQ0001ABC", 1, "file.html#IG-REQ0001ABC-01"),
    ("folder/file.md", "IG-REQ0001ABC", 2, "file.html#IG-REQ0001ABC-02"),
    ("folder/file.md", "IG-REQ0001ABC", 3, "file.html#IG-REQ0001ABC-03"),
    ("folder/file.md", "IG-REQ0001ABC", 4, "file.html#IG-REQ0001ABC-04"),
    ("folder/file.md", "IG-REQ0001ABC", 5, "file.html#IG-REQ0001ABC-05"),
    ("folder/file.md", "IG-REQ0001ABC", 6, "file.html#IG-REQ0001ABC-06"),
    ("folder/file.md", "IG-REQ0001ABC", 7, "file.html#IG-REQ0001ABC-07"),
    ("folder/file.md", "IG-REQ0001ABC", 8, "file.html#IG-REQ0001ABC-08"),
    ("folder/file.md", "IG-REQ0001ABC", 9, "file.html#IG-REQ0001ABC-09"),
    ("folder/file.md", "IG-REQ0001ABC", 10, "file.html#IG-REQ0001ABC-10"),
    ("folder/file.md", "IG-REQ0001ABC", 15, "file.html#IG-REQ0001ABC-15"),
    ("folder/file.md", "IG-REQ0001ABC", 100, "file.html#IG-REQ0001ABC-100"),
    ("folder/file.md", "IG-REQ0001ABC", 146, "file.html#IG-REQ0001ABC-146"),
])
def test_convert_to_link(source, key, version, expected):
    assert utils.convert_to_link(source, key=key, version=version) == expected


@pytest.mark.parametrize("base, source, key, version, expected", [
    ("https://www.example.com/1.2.0", "folder/file.md", None, None, "https://www.example.com/1.2.0/file.html"),
    ("https://www.example.com/1.2.0", "folder/file.xml", "IG-REQ-0000001", None, "https://www.example.com/1.2.0/file.html#IG-REQ-0000001"),
    ("https://www.example.com/1.2.0", "folder/file.md", "IG-REQ-0000001", 2, "https://www.example.com/1.2.0/file.html#IG-REQ-0000001-02"),
    ("https://www.example.com/1.2.0", "folder/file.md", None, 2, "https://www.example.com/1.2.0/file.html"),
    ("https://www.example.com/1.2.0", "folder/file.md", "IG-REQ0001ABC", 0, "https://www.example.com/1.2.0/file.html#IG-REQ0001ABC"),
    ("https://www.example.com/1.2.0", "folder/file.md", "IG-REQ0001ABC", 1, "https://www.example.com/1.2.0/file.html#IG-REQ0001ABC-01"),
    ("https://www.example.com/1.2.0", "folder/file.md", "IG-REQ0001ABC", 2, "https://www.example.com/1.2.0/file.html#IG-REQ0001ABC-02"),
    ("https://www.example.com/1.2.0", "folder/file.md", "IG-REQ0001ABC", 3, "https://www.example.com/1.2.0/file.html#IG-REQ0001ABC-03"),
    ("https://www.example.com/1.2.0", "folder/file.md", "IG-REQ0001ABC", 4, "https://www.example.com/1.2.0/file.html#IG-REQ0001ABC-04"),
    ("https://www.example.com/1.2.0", "folder/file.md", "IG-REQ0001ABC", 5, "https://www.example.com/1.2.0/file.html#IG-REQ0001ABC-05"),
    ("https://www.example.com/1.2.0", "folder/file.md", "IG-REQ0001ABC", 6, "https://www.example.com/1.2.0/file.html#IG-REQ0001ABC-06"),
    ("https://www.example.com/1.2.0", "folder/file.md", "IG-REQ0001ABC", 7, "https://www.example.com/1.2.0/file.html#IG-REQ0001ABC-07"),
    ("https://www.example.com/1.2.0", "folder/file.md", "IG-REQ0001ABC", 8, "https://www.example.com/1.2.0/file.html#IG-REQ0001ABC-08"),
    ("https://www.example.com/1.2.0", "folder/file.md", "IG-REQ0001ABC", 9, "https://www.example.com/1.2.0/file.html#IG-REQ0001ABC-09"),
    ("https://www.example.com/1.2.0", "folder/file.md", "IG-REQ0001ABC", 10, "https://www.example.com/1.2.0/file.html#IG-REQ0001ABC-10"),
    ("https://www.example.com/1.2.0", "folder/file.md", "IG-REQ0001ABC", 15, "https://www.example.com/1.2.0/file.html#IG-REQ0001ABC-15"),
    ("https://www.example.com/1.2.0", "folder/file.md", "IG-REQ0001ABC", 100, "https://www.example.com/1.2.0/file.html#IG-REQ0001ABC-100"),
    ("https://www.example.com/1.2.0", "folder/file.md", "IG-REQ0001ABC", 146, "https://www.example.com/1.2.0/file.html#IG-REQ0001ABC-146"),
])
def test_convert_to_ig_link(base, source, key, version, expected):
    assert utils.convert_to_ig_requirement_link(base, source, key=key, version=version) == expected


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
