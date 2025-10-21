import os
import json
import yaml

from ..utils import convert_to_link
from ..errors import ReleaseNotesOutputPathNotExists, ExportFormatUnknown
from .release import ReleaseManager



class RequirementExporter:
    EXPORT_BASE_FILENAME = "requirements"

    def __init__(self, config, format, version=None):
        self.release_manager = ReleaseManager(config)
        self.format = format
        self.version = version

    def export(self, output, with_deleted=False):
        if self.version is None or self.version == "current":
            release = self.release_manager.load()
        else:
            release = self.release_manager.load_version(version=self.version)
        requirements = []
        for req in release.requirements:
            if req.is_deleted and not with_deleted:
                continue
            data = req.serialize()
            data["path"] = convert_to_link(req.source)
            data["release"] = release.version
            requirements.append(data)
        self.save_export(output=output, data=requirements)

    @classmethod
    def generate_filename(cls, format, version):
        fmt = str(format).upper()
        if fmt == "JSON":
            extension = ".json"
        elif fmt == "YAML":
            extension = ".yaml"
        else:
            raise ExportFormatUnknown(f"The format {format} is not supported.")
        base = f"{cls.EXPORT_BASE_FILENAME}-{version}" if version and version != "current" else cls.EXPORT_BASE_FILENAME
        return f"{base}{extension}"

    @classmethod
    def generate_filepath(cls, output, format, version):
        _, output_ext = os.path.splitext(output)
        if output_ext:
            filepath = output
        else:
            filename = cls.generate_filename(format=format, version=version)
            filepath = os.path.join(output, filename)
        return filepath

    def save_export(self, output, data):
        ext_map = {
            '.json': 'JSON',
            '.yaml': 'YAML',
            '.yml': 'YAML'
        }
        filepath = self.generate_filepath(output=output, format=self.format, version=self.version)

        base, ext = os.path.splitext(filepath)
        file_format = ext_map.get(ext.lower())
        if file_format is None:
            raise ExportFormatUnknown(f"The format {ext} is not supported.")

        out_dir = os.path.dirname(filepath) or "."
        if not os.path.exists(out_dir):
            raise ReleaseNotesOutputPathNotExists(f"Path {out_dir} does not exists.")
        if file_format == 'JSON':
            with open(filepath, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
        elif file_format == 'YAML':
            with open(filepath, 'w', encoding='utf-8') as file:
                yaml.dump(data, file, default_flow_style=False, allow_unicode=True)
        
