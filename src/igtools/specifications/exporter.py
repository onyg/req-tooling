import os
import yaml

from ..utils import clean_list, convert_to_link
from ..errors import ReleaseNotesOutputPathNotExists, ExportFormatUnknown
from .manager import ReleaseManager



class RequirementExporter:
    EXPORT_FILENAME = "requirements.yaml"

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
                    link=convert_to_link(req.source, key=req.key, version=req.version)
                ))
        self.save_export(output=output, data=requirements)

    def save_export(self, output, data):
        filepath = os.path.join(output, self.filename)
        if not os.path.exists(output):
            raise ReleaseNotesOutputPathNotExists(f"Path {output} does not exists.")
        if self.format == 'YAML':
            with open(filepath, 'w', encoding='utf-8') as file:
                yaml.dump(data, file, default_flow_style=False, allow_unicode=True)
        else:
            raise ExportFormatUnknown(f"The format {self.format} is not supported.")
        
