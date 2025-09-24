import os
import json
import yaml

from ..utils import convert_to_link
from ..errors import FilePathNotExists, ExportFormatUnknown
from .manager import ReleaseManager



class PolarionExporter:
    EXPORT_BASE_FILENAME = "polarion-requirements"
    SUSHI_CONFIG = "sushi-config.yaml"


    def __init__(self, config, sushi_config=None, filename=None, version=None):
        self.config = config
        self.release_manager = ReleaseManager(config)
        self.sushi_config = sushi_config or self.SUSHI_CONFIG
        self.__filename = filename
        self.version = version

    @classmethod
    def generate_filename(cls, version):
        fmt = str(format).upper()
        extension = ".json"
        base = f"{cls.EXPORT_BASE_FILENAME}-{version}" if version and version != "current" else cls.EXPORT_BASE_FILENAME
        return f"{base}{extension}"

    @property
    def filename(self):
        if self.__filename:
            return self.__filename
        else:
            return self.generate_filename(self.version)

    def export(self, output):
        if self.version is None or self.version == "current":
            release = self.release_manager.load()
        else:
            release = self.release_manager.load_version(version=self.version)
        requirements = []
        for req in release.requirements:
            data = req.serialize()
            data["path"] = convert_to_link(req.source)
            data["release"] = release.version
            requirements.append(data)
        self.save_export(output=output, data=requirements)


    def save_export(self, output, data):
        ext_map = {
            '.json': 'JSON'
        }
        base, ext = os.path.splitext(self.filename)

        if ext.lower() not in ext_map:
            raise ExportFormatUnknown(f"Unsupported file extension: '{ext}'")
        filename = self.filename
        
        filepath = os.path.join(output, self.filename)

        file_format = ext_map.get(ext.lower())
        if not os.path.exists(output):
            raise FilePathNotExists(f"Path {output} does not exists.")
        if file_format == 'JSON':
            with open(filepath, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
        else:
            raise ExportFormatUnknown(f"The format {file_format} is not supported.")
        