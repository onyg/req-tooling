import enum
from datetime import datetime

class State(enum.Enum):
    NEW = 'new'
    STABLE = 'stable'
    MODIFIED = 'modified'
    DELETED = 'deleted'
    MOVED = 'moved'


class Requirement(object):

    def __init__(self):
        self.id = None
        self.title = None
        self.target = None
        self.version = 0
        self.status = State.NEW.value
        self.source = None
        self.text = ""
        self._created = None
        self._modified = None
        self._deleted = ""

    def _from_datetime(self, value):
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, str):
            try:
                datetime.fromisoformat(value)
            except ValueError:
                raise ValueError("Invalid date string format. Must be ISO 8601.")
            return value
        elif not value:
            return value
        else:
            raise TypeError("Created must be a datetime object or ISO 8601 string.")

    def _to_datetime(self, value):
        if value:
            return datetime.fromisoformat(value)
        return None

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

    def deserialize(self, data):
        self.id = data.get('id')
        self.title = data.get('title')
        self.target = data.get('target')
        self.version = data.get('version')
        self.status = data.get('status')
        self.source = data.get('source')
        self.text = data.get('text')
        self._created = data.get('created', '')
        self._modified = data.get('modified', '')
        self._deleted = data.get('deleted', '')
        return self

    def serialize(self):
        serialized = dict(
            id=self.id,
            title=self.title,
            target=self.target,
            version=self.version,
            status=self.status,
            source=self.source,
            text=self.text,
            created=self._created,
            modified=self._modified
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