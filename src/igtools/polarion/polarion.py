import os
import json
import yaml
import importlib.resources as resources
from functools import lru_cache

from ..utils import utils, cli
from ..errors import FilePathNotExists, ExportFormatUnknown, BaseException
from ..specifications import ReleaseManager

# funkt. Eignung: Test Produkt/FA
DEFAULT_TESTPROCEDURE = "testProcedurePT03" 

class PolarionExportMappingError(BaseException):
    pass


@lru_cache(maxsize=1)
def load_polarion_mappings():
    with resources.files("igtools").joinpath("mappings/polarion.yaml").open("r", encoding="utf-8") as f:
        mappings = yaml.safe_load(f)
    return mappings.get("actor_to_product", {}), mappings.get("testproc_to_id", {})


class PolarionExporter:
    EXPORT_BASE_FILENAME = "polarion-requirements"

    def __init__(self, config, ig_config, filename=None, version=None, default_test_procedure=None):
        self.config = config
        self.release_manager = ReleaseManager(config)
        self.ig_config = ig_config
        self.__filename = filename
        self.version = version
        self.default_tp = default_test_procedure or DEFAULT_TESTPROCEDURE

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

    def get_test_procedure(self, key, requirement):
        ACTOR_MAPPING, TESTPROC_MAPPING = load_polarion_mappings()
        procedure = TESTPROC_MAPPING.get(key, None)
        if procedure is None:
            raise PolarionExportMappingError(f"No test procedure mapping found for '{key}'. Source: {requirement.source}; requirement key: {requirement.key}.")
        return procedure

    def map_product_types(self, requirement):
        ACTOR_MAPPING, TESTPROC_MAPPING = load_polarion_mappings()
        product_types = []
        try:
            for actor, test_procedure in requirement.test_procedures.items():
                product = ACTOR_MAPPING.get(actor, None)
                if product is None:
                    raise PolarionExportMappingError(f"No product type mapping found for actor '{actor}'. Source: {requirement.source}; requirement key: {requirement.key}.")
                product_type = {}
                product_type["product_type"] = product
                product_type["test_procedure"] = []
                for tp in test_procedure:
                    procedure = self.get_test_procedure(key=tp, requirement=requirement)
                    product_type["test_procedure"].append(procedure)
                if len(product_type["test_procedure"]) == 0:
                    procedure = self.get_test_procedure(key=self.default_tp, requirement=requirement)
                    product_type["test_procedure"].append(procedure)

                product_types.append(product_type)
        except AttributeError as e:
            cli.print_error(f"AttributeError: {e}; Source: {requirement.source}; requirement key: {requirement.key}.")
        return product_types

    def export(self, output):
        if self.version is None or self.version == "current":
            release = self.release_manager.load()
        else:
            release = self.release_manager.load_version(version=self.version)
        requirements = []
        for req in release.requirements:
            _data = req.serialize()

            product_types = self.map_product_types(requirement=req)

            data = {}
            data["document_id"] = self.ig_config.name
            data["document_title"] = self.ig_config.title
            data["document_link"] = self.ig_config.link
            data["key"] = req.key
            data["title"] = req.title
            data["version"] = req.version
            data["status"] = req.status
            data["text"] = req.text
            data["conformance"] = req.conformance
            data["product_types"] = product_types
            data["link"] = utils.convert_to_ig_requirement_link(base=self.ig_config.link,
                                                                source=req.source,
                                                                key=req.key,
                                                                version=req.version)
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
        