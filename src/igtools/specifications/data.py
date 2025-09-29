import enum
from datetime import datetime

from ..utils import validate_type, to_str, to_list

class ReleaseState(enum.Enum):
    NEW = 'NEW'
    STABLE = 'STABLE'
    MODIFIED = 'MODIFIED'
    DELETED = 'DELETED'
    MARKED_FOR_DELETION = 'MARKED_FOR_DELETION'
    MOVED = 'MOVED'


class PublicationStatus(enum.Enum):
    DRAFT = 'DRAFT'
    ACTIVE = 'ACTIVE'
    RETIRED = 'RETIRED'
    UNKNOWN = 'UNKNOWN'

class Requirement(object):

    def __init__(self, key=None, title=None, text=None, actor=None, source=None, version=None, process=None, conformance=None, status=None, test_procedures=None):
        self.key = key
        self.title = title
        self.actor = actor
        self.version = version
        self.release_status = process or ReleaseState.NEW.value
        self.status = status or PublicationStatus.ACTIVE.value
        self.source = source
        self.text = text
        self._created =  ""
        self._modified = ""
        self._deleted = ""
        self._date = ""
        self.conformance = conformance or ""
        self.test_procedures = test_procedures or {}


    def _from_datetime(self, value):
        if not value:
            return value
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, str):
            try:
                datetime.fromisoformat(value)
            except ValueError:
                raise ValueError("Invalid date string format. Must be ISO 8601.")
            return value
        else:
            raise TypeError("Created must be a datetime object or ISO 8601 string.")

    def _to_datetime(self, value):
        if value:
            return datetime.fromisoformat(value)
        return None

    @property
    def date(self):
        return self._to_datetime(value=self._date)

    @date.setter
    def date(self, value):
        self._date = self._from_datetime(value=value)

    @property
    def created(self):
        return self._to_datetime(value=self._created)

    @created.setter
    def created(self, value):
        self._created = self._from_datetime(value=value)

    @property
    def modified(self):
        return self._to_datetime(value=self._modified)

    @modified.setter
    def modified(self, value):
        self._modified = self._from_datetime(value=value)

    @property
    def deleted(self):
        return self._to_datetime(value=self._deleted)

    @deleted.setter
    def deleted(self, value):
        self._deleted = self._from_datetime(value=value)

    @property
    def is_stable(self):
        return self.release_status == ReleaseState.STABLE.value
    
    @is_stable.setter
    @validate_type(bool)
    def is_stable(self, value: bool):
        if value:
            self.release_status = ReleaseState.STABLE.value
            self.status = PublicationStatus.ACTIVE.value

    @property
    def is_new(self):
        return self.release_status == ReleaseState.NEW.value
    
    @is_new.setter
    @validate_type(bool)
    def is_new(self, value: bool):
        if value:
            self.release_status = ReleaseState.NEW.value
            self.status = PublicationStatus.ACTIVE.value

    @property
    def is_modified(self):
        return self.release_status == ReleaseState.MODIFIED.value
    
    @is_modified.setter
    @validate_type(bool)
    def is_modified(self, value: bool):
        if value:
            self.release_status = ReleaseState.MODIFIED.value
            self.status = PublicationStatus.ACTIVE.value

    @property
    def is_deleted(self):
        return self.release_status == ReleaseState.DELETED.value or self.release_status == ReleaseState.MARKED_FOR_DELETION.value
    
    @is_deleted.setter
    @validate_type(bool)
    def is_deleted(self, value: bool):
        if value:
            self.release_status = ReleaseState.DELETED.value
            self.status = PublicationStatus.RETIRED.value

    @property
    def for_deletion(self):
        return self.release_status == ReleaseState.MARKED_FOR_DELETION.value
    
    @for_deletion.setter
    @validate_type(bool)
    def for_deletion(self, value: bool):
        if value:
            self.release_status = ReleaseState.MARKED_FOR_DELETION.value
            self.status = PublicationStatus.RETIRED.value

    @property
    def is_moved(self):
        return self.release_status == ReleaseState.MOVED.value
    
    @is_moved.setter
    @validate_type(bool)
    def is_moved(self, value: bool):
        if value:
            self.release_status = ReleaseState.MOVED.value
            self.status = PublicationStatus.ACTIVE.value

    @property
    def actor_as_list(self):
        return to_list(self.actor)
    
    @property
    def actor_as_str(self):
        return to_str(self.actor)

    def deserialize(self, data):
        if data is None:
            return self
        self.key = data.get('key')
        self.title = data.get('title')
        self.actor = to_str(data.get('actor'))
        self.test_procedures = data.get('test_procedures', [])
        self.version = data.get('version')
        self.release_status = data.get('release_status')
        self.status = data.get('status')
        self.source = data.get('source')
        self.text = data.get('text')
        self.conformance = data.get('conformance', '')
        self._created = data.get('created', '')
        self._modified = data.get('modified', '')
        self._deleted = data.get('deleted', '')
        self._date = data.get('date', '')
        return self

    def serialize(self):
        serialized = dict(
            key=self.key,
            title=self.title,
            actor=self.actor_as_list,
            test_procedures=self.test_procedures,
            version=self.version,
            release_status=self.release_status,
            status=self.status,
            source=self.source,
            text=self.text,
            conformance=self.conformance,
            created=self._created,
            modified=self._modified,
            date=self._date
        )
        if self._deleted:
            serialized['deleted'] = self._deleted
        return serialized


class Release(object):

    def __init__(self, name=None, version=None):
        self.name = name or ""
        self.version = version or ""
        self.requirements = []
        self.archive = []

    def deserialize(self, data):
        self.name = data.get('name')
        self.version = data.get('version')
        self.requirements = []
        for r in data.get('requirements', []):
            self.requirements.append(Requirement().deserialize(data=r))
        return self

    def serialize(self):
        _requirements = []
        for r in self.requirements:
            _requirements.append(r.serialize())
        return dict(
            name=self.name,
            version=self.version,
            requirements=_requirements
        )