import os
import json

from .release import ReleaseManager
from ..errors import ReleaseNotesOutputPathNotExists
from ..utils import convert_to_link



class ReleaseNoteManager(object):
    RELEASE_NOTES_FILENAME = "release-notes.json"

    def __init__(self, config, filename=None):
        self.config = config
        self.release_manager = ReleaseManager(config=self.config)
        self.filename = filename or self.RELEASE_NOTES_FILENAME

    def generate(self, output):
        filepath = os.path.join(output, self.filename)
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
                    actor=req.actor_as_list,
                    version=req.version,
                    release_status=req.release_status.upper(),
                    status=req.status.upper(),
                    conformance=req.conformance,
                    path=convert_to_link(req.source)
                ))
            releases.append(release)
        
        notes = dict(
            releases=list(reversed(releases))
        )

        if not os.path.exists(output):
            raise ReleaseNotesOutputPathNotExists(f"Path {output} does not exists.")
        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(notes, file, indent=4, ensure_ascii=False)


    
