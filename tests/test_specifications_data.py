import pytest
from datetime import datetime
from igtools.specifications.data import Requirement, Release, ReleaseState, PublicationStatus


def test_requirement_basic_properties():
    r = Requirement(key="IG-PTY01234A23", title="Test", actor="EPA-Medication-Service", version="0", status="DRAFT")

    assert r.key == "IG-PTY01234A23"
    assert r.title == "Test"
    assert r.actor == "EPA-Medication-Service"
    assert r.version == "0"
    assert r.status == "DRAFT"
    assert r.is_new
    assert not r.is_stable
    assert r.actor_as_list == ["EPA-Medication-Service"]
    assert r.actor_as_str == "EPA-Medication-Service"


def test_requirement_state_switches():
    r = Requirement()

    r.is_stable = True
    assert r.release_status == ReleaseState.STABLE.value
    assert r.status == PublicationStatus.ACTIVE.value

    r.is_modified = True
    assert r.release_status == ReleaseState.MODIFIED.value
    assert r.status == PublicationStatus.ACTIVE.value

    r.is_moved = True
    assert r.release_status == ReleaseState.MOVED.value
    assert r.status == PublicationStatus.ACTIVE.value

    r.for_deletion = True
    assert r.release_status == ReleaseState.MARKED_FOR_DELETION.value
    assert r.status == PublicationStatus.RETIRED.value
    assert r.is_deleted

    r.is_deleted = True
    assert r.release_status == ReleaseState.DELETED.value
    assert r.status == PublicationStatus.RETIRED.value
    assert r.is_deleted


def test_requirement_date_properties():
    now = datetime.now().replace(microsecond=0)
    r = Requirement()
    r.created = now
    r.modified = now.isoformat()
    r.date = now
    r.deleted = ""

    assert r.created == now
    assert r.modified == now
    assert r.date == now
    assert r.deleted is None


def test_requirement_date_invalid_type():
    r = Requirement()
    with pytest.raises(TypeError):
        r.created = 12345

    with pytest.raises(ValueError):
        r.created = "not-a-date"


def test_requirement_serialize_deserialize():
    data = {
        "key": "IG-PTY01234A23",
        "title": "Title",
        "actor": ["EPA-Medication-Service", "EPA-Audit-Service"],
        "version": "1",
        "release_status": "MODIFIED",
        "status": "ACTIVE",
        "source": "source.txt",
        "text": "Requirement text",
        "conformance": "SHALL",
        "created": "2024-01-01T00:00:00",
        "modified": "2024-01-02T00:00:00",
        "deleted": "2024-01-03T00:00:00",
        "date": "2024-01-04T00:00:00"
    }

    r = Requirement().deserialize(data)
    assert r.key == "IG-PTY01234A23"
    assert r.actor_as_list == ["EPA-Medication-Service", "EPA-Audit-Service"]
    assert r.actor_as_str == "EPA-Medication-Service, EPA-Audit-Service"
    result = r.serialize()
    assert result["key"] == "IG-PTY01234A23"
    assert result["created"] == "2024-01-01T00:00:00"
    assert result["deleted"] == "2024-01-03T00:00:00"


def test_release_serialize_deserialize():
    req_data = {
        "key": "IG-PTY01234A23",
        "title": "Title",
        "actor": "EPA-Medication-Service",
        "version": "1",
        "text": "Text"
    }
    release_data = {
        "name": "Release A",
        "version": "1.0.0",
        "requirements": [req_data]
    }

    rel = Release().deserialize(release_data)
    assert rel.name == "Release A"
    assert rel.version == "1.0.0"
    assert len(rel.requirements) == 1
    assert isinstance(rel.requirements[0], Requirement)

    result = rel.serialize()
    assert result["name"] == "Release A"
    assert result["version"] == "1.0.0"
    assert isinstance(result["requirements"], list)
    assert result["requirements"][0]["key"] == "IG-PTY01234A23"


def test_enums():
    assert ReleaseState.NEW.value == "NEW"
    assert PublicationStatus.RETIRED.name == "RETIRED"
