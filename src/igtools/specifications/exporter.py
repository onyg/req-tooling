import os
import json

from ..utils import convert_to_link
from ..errors import ReleaseNotesOutputPathNotExists, ExportFormatUnknown
from .manager import ReleaseManager



class RequirementExporter:
    EXPORT_FILENAME = "requirements.json"

    def __init__(self, config, format, filename=None):
        self.config = config
        self.release_manager = ReleaseManager(config)
        self.format = format
        self.filename = filename or self.EXPORT_FILENAME

    def export(self, output):
        release = self.release_manager.load()
        requirements = []
        for req in release.requirements:
            if not req.is_deleted:
                requirements.append(dict(
                    title=req.title,
                    key=req.key,
                    actor=req.actor_as_list,
                    version=req.version,
                    releasestatus=req.release_status.upper(),
                    status=req.status.upper(),
                    text=req.text,
                    source=req.source,
                    conformance=req.conformance,
                    path=convert_to_link(req.source)
                ))
        self.save_export(output=output, data=requirements)

    def save_export(self, output, data):
        filepath = os.path.join(output, self.filename)
        if not os.path.exists(output):
            raise ReleaseNotesOutputPathNotExists(f"Path {output} does not exists.")
        if self.format == 'JSON':
            with open(filepath, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
        else:
            raise ExportFormatUnknown(f"The format {self.format} is not supported.")
        
