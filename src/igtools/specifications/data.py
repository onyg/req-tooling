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

    @property
    def created(self):
        if self._created:
            return datetime.fromisoformat(self._created)
        return None

    @created.setter
    def created(self, value):
        if isinstance(value, datetime):
            self._created = value.isoformat()
        elif isinstance(value, str):
            try:
                datetime.fromisoformat(value)
                self._created = value
            except ValueError:
                raise ValueError("Invalid date string format. Must be ISO 8601.")
        else:
            raise TypeError("Created must be a datetime object or ISO 8601 string.")

    @property
    def modified(self):
        if self._modified:
            return datetime.fromisoformat(self._modified)
        return None

    @modified.setter
    def modified(self, value):
        if isinstance(value, datetime):
            self._modified = value.isoformat()
        elif isinstance(value, str):
            try:
                datetime.fromisoformat(value)
                self._modified = value
            except ValueError:
                raise ValueError("Invalid date string format. Must be ISO 8601.")
        else:
            raise TypeError("Modified must be a datetime object or ISO 8601 string.")
    

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
        return self

    def serialize(self):
        return dict(
            id=self.id,
            title=self.title,
            target=self.target,
            version=self.version,
            status=self.status,
            source=self.source,
            text=self.text,
            created=self._created,
            modified= self._modified
        )


class Release(object):

    def __init__(self, name=None, version=None):
        self.name = name or ""
        self.version = version or ""
        self.requirements = []

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