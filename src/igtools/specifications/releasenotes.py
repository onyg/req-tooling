import os
import json

from .release import ReleaseManager
from ..errors import ReleaseNotesOutputPathNotExists, ExportFormatUnknown
from ..utils import convert_to_link



class ReleaseNoteManager(object):
    RELEASE_NOTES_FILENAME = "release-notes.json"

    def __init__(self, config):
        self.config = config
        self.release_manager = ReleaseManager(config=self.config)

    @classmethod
    def generate_filepath(cls, output):
        _, output_ext = os.path.splitext(output)
        if output_ext:
            filepath = output
        else:
            base = cls.RELEASE_NOTES_FILENAME
            filepath = os.path.join(output, base)
        return filepath

    def generate(self, output):
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
        self.save_export(output=output, data=notes)

    def save_export(self, output, data):
        ext_map = {
            '.json': 'JSON'
        }
        filepath = self.generate_filepath(output=output)
        base, ext = os.path.splitext(filepath)
        if ext.lower() not in ext_map:
            raise ExportFormatUnknown(f"Unsupported file extension: '{ext}'")

        file_format = ext_map[ext.lower()]

        dir_path = os.path.dirname(filepath) or '.'
        if not os.path.exists(dir_path):
            raise ReleaseNotesOutputPathNotExists(f"Path {dir_path} does not exist.")

        if file_format == 'JSON':
            with open(filepath, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
        else:
            raise ExportFormatUnknown(f"The format {file_format} is not supported.")



    
