import os
import yaml

from .manager import ReleaseManager
from ..errors import ReleaseNotesOutputPathNotExists


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
                if req.is_stable:
                    continue
                release['requirements'].append(dict(
                    title=req.title,
                    key=req.key,
                    actor=req.actor,
                    version=req.version,
                    status=req.status.upper(),
                    conformance=req.conformance
                ))
            releases.append(release)
        
        notes = dict(
            releases=list(reversed(releases))
        )

        if not os.path.exists(output):
            raise ReleaseNotesOutputPathNotExists(f"Path {output} does not exists.")
        with open(filepath, 'w', encoding='utf-8') as file:
            yaml.dump(notes, file, default_flow_style=False, allow_unicode=True)


    
