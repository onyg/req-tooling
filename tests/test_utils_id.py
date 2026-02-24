import re
import pytest

from unittest.mock import MagicMock

from igtools.utils import id as id_utils


@pytest.fixture
def mock_config():
    return MagicMock(
        prefix="REQ",
        separator="-",
        scope="PYT",
        key_mode="random",
        current_req_number=0
    )


@pytest.fixture(autouse=True)
def clear_current_ids():
    id_utils.current_ids.clear()


def test_add_and_check_id():
    test_id = "12345A67"
    assert not id_utils.is_already_added(test_id)
    assert id_utils.add_id(test_id) is True
    assert id_utils.is_already_added(test_id) is True
    assert id_utils.add_id(test_id) is False


def test_create_id_length_and_charset():
    charset = "ABCDEF"
    id_length = 10
    generated_id = id_utils.create_id(length=id_length, charset=charset)
    assert len(generated_id) == id_length
    assert all(c in charset for c in generated_id)


def test_generate_id_default():
    generated_id = id_utils.generate_id()
    assert len(generated_id) == 8  # 5 digits + 1 alpha + 2 alphanum
    assert re.match(r'^\d{5}[ABCDEFGHJKLMNPQRSTUVWXYZ][0-9ABCDEFGHJKLMNPQRSTUVWXYZ]{2}$', generated_id)


def test_generate_id_with_prefix_and_scope():
    prefix = "PFX-"
    scope = "SCP"
    generated_id = id_utils.generate_id(prefix=prefix, scope=scope)
    assert generated_id.startswith(prefix + scope)
    assert len(generated_id) == len(prefix) + len(scope) + 8  # Prefix + Scope + ID


def test_unique_generation():
    prefix = "PFX-"
    scope = "SCP"
    ids = set()
    for _ in range(1000000):
        new_id = id_utils.generate_id(prefix=prefix, scope=scope)
        assert new_id not in ids
        ids.add(new_id)


def test_sequential_id_generator_respects_existing_max(mock_config):
    existing_keys = [
        "REQ-PYT1",
        "REQ-PYT02",
        "REQ-PYT10",
        "OTHER-99",   # should be ignored
        "REQ-OTHER3"  # should be ignored
    ]
    mock_config.current_req_number = 5  # config has 5, but existing has 10
    generator = id_utils.SequentialIdGenerator(config=mock_config, existing_keys=existing_keys)

    assert generator.generate() == "REQ-PYT11"
    assert generator.generate() == "REQ-PYT12"


def test_sequential_id_generator_respects_config_counter(mock_config):
    mock_config.current_req_number = 12
    existing_keys = ["REQ-PYT1", "REQ-PYT5"]
    generator = id_utils.SequentialIdGenerator(config=mock_config, existing_keys=existing_keys)

    assert generator.generate() == "REQ-PYT13"