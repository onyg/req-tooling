import os
import yaml

from .manager import ReleaseManager
from .data import State


RELEASE_NOTES_FILENAME = "release-notes.yaml"


class ReleaseNoteManager(object):

    def __init__(self, config):
        self.config = config
        self.release_manager = ReleaseManager(config=self.config)

    def generate(self, output):
        filepath = os.path.join(output, RELEASE_NOTES_FILENAME)
        releases = []
        for version in self.config.releases:
            release = dict(version=version, requirements=[])
            data = self.release_manager.load_version(version=version)
            for req in data.requirements:
                if req.status == State.STABLE.value:
                    continue
                release['requirements'].append(dict(
                    title=req.title,
                    id=req.id,
                    target=req.target,
                    version=req.version,
                    status=req.status.upper()
                ))
            releases.append(release)
        
        notes = dict(
            releases=list(reversed(releases))
        )

        if not os.path.exists(output):
            raise Exception(f"TODO: Path {output} does not exists.")
        with open(filepath, 'w', encoding='utf-8') as file:
            yaml.dump(notes, file, default_flow_style=False, allow_unicode=True)


    
