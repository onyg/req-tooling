import os
import json
import yaml

from ..utils import convert_to_link
from ..errors import ReleaseNotesOutputPathNotExists, ExportFormatUnknown
from .manager import ReleaseManager



class RequirementExporter:
    EXPORT_BASE_FILENAME = "requirements"

    def __init__(self, config, format, filename=None, version=None):
        self.config = config
        self.release_manager = ReleaseManager(config)
        self.format = format
        self.__filename = filename
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

    @property
    def filename(self):
        if self.__filename:
            return self.__filename
        else:
            return self.generate_filename(self.format, self.version)

    def save_export(self, output, data):
        ext_map = {
            '.json': 'JSON',
            '.yaml': 'YAML',
            '.yml': 'YAML'
        }
        base, ext = os.path.splitext(self.filename)
        if not ext:
            fmt = str(self.format).upper()
            ext = '.json' if fmt == 'JSON' else '.yaml'
            filename = base + ext
        else:
            if ext.lower() not in ext_map:
                raise ExportFormatUnknown(f"Unsupported file extension: '{ext}'")
            filename = self.filename
        
        filepath = os.path.join(output, filename)

        file_format = ext_map.get(ext.lower())
        if not os.path.exists(output):
            raise ReleaseNotesOutputPathNotExists(f"Path {output} does not exists.")
        if file_format == 'JSON':
            with open(filepath, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
        elif file_format == 'YAML':
            with open(filepath, 'w', encoding='utf-8') as file:
                yaml.dump(data, file, default_flow_style=False, allow_unicode=True)
        else:
            raise ExportFormatUnknown(f"The format {file_format} is not supported.")
        
