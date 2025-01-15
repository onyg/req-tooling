import os
import shutil
import yaml

from ..errors import FilepathNotExists

FHIR_EXTRACT_CONFIG_FILENAME = "igtools-fhir-extractor.yaml"
FHIR_FOLDERS = [
    os.path.join(os.path.expanduser("~"), ".fhir", "packages"),
    os.path.join(os.getcwd(), ".fhir", "packages"),
    os.path.join(os.getcwd(), "dependencies")
]

class FHIRPackageExtractor:

    def __init__(self, config):
        self.config = config

    def process(self, config_filename=None):
        config_filename = config_filename or FHIR_EXTRACT_CONFIG_FILENAME

        if not os.path.exists(config_filename):
            raise FilepathNotExists(f"FHIR extract config file '{config_filename}' not found.")

        with open(config_filename, 'r') as _file:
            extract_config = yaml.safe_load(_file)

        output_folder = extract_config['output']
        self._prepare_output_folder(output_folder)

        packages = extract_config['packages']
        
        for package_name, resources in packages.items():
            version = resources['version']
            resource_list = resources['resources']
            
            for resource in resource_list:
                self._process_resource(package_name, version, resource, output_folder)

    def _prepare_output_folder(self, output_folder):
        if os.path.exists(output_folder):
            shutil.rmtree(output_folder)
        os.makedirs(output_folder, exist_ok=True)

    def _process_resource(self, package_name, version, resource, output_folder):
        resource_type, resource_id = resource.split('/')
        possible_filenames = self._generate_possible_filenames(resource_type, resource_id)

        for fhir_folder in FHIR_FOLDERS:
            package_folder = os.path.join(fhir_folder, f"{package_name}#{version}", "package")

            for resource_filename in possible_filenames:
                resource_path = os.path.join(package_folder, resource_filename)
                if os.path.exists(resource_path):
                    self._copy_resource(resource_path, output_folder)
                    return  # Exit once the resource is found and copied

        print(f"Resource {resource_type}/{resource_id} not found in directories {FHIR_FOLDERS}")

    def _generate_possible_filenames(self, resource_type, resource_id):
        return [
            f"{resource_type}-{resource_id}.json",
            f"{resource_id}.{resource_type}.json",
            f"{resource_type}-{resource_id}.xml",
            f"{resource_id}.{resource_type}.xml",
            os.path.join(resource_type, f"{resource_id}.xml"),
            os.path.join(resource_type, f"{resource_id}.json")
        ]

    def _copy_resource(self, resource_path, output_folder):
        target_path = os.path.join(output_folder, os.path.basename(resource_path))
        shutil.copy(resource_path, target_path)
        print(f"Copied {os.path.basename(resource_path)} to {target_path}")
