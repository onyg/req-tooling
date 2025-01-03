import enum


class State(enum.Enum):
    NEW = 'new'
    STABLE = 'stable'
    CHANGE = 'change'
    DELETED = 'deleted'


class Requirement(object):

    def __init__(self):
        self.id = None
        self.title = None
        self.target = None
        self.version = 0
        self.status = State.NEW.value
        self.source = None
        self.text = ""

    def deserialize(self, data):
        self.id = data.get('id')
        self.title = data.get('title')
        self.target = data.get('target')
        self.version = data.get('version')
        self.status = data.get('status')
        self.source = data.get('source')
        self.text = data.get('text')
        return self

    def serialize(self):
        return dict(
            id=self.id,
            title=self.title,
            target=self.target,
            version=self.version,
            status=self.status,
            source=self.source,
            text=self.text
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