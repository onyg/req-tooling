import os
import shutil
import yaml
import requests
import tarfile
from ..errors import FilePathNotExists, FileFormatException, DownloadException
from ..utils import cli

FHIR_EXTRACT_CONFIG_FILENAME = "igtools-fhir-extractor.yaml"
FHIR_FOLDERS = [
    os.path.join(os.path.expanduser("~"), ".fhir", "packages"),
    os.path.join(os.getcwd(), ".fhir", "packages"),
    os.path.join(os.getcwd(), "dependencies")
]

FHIR_PACKAGE_REGISTRY_URL = "https://packages.fhir.org"
FHIR_PACKAGE_DOWNLOAD_FOLDER = ".temp"


class FHIRPackageExtractor:

    def __init__(self, config):
        self.config = config
        self.download_folder = FHIR_PACKAGE_DOWNLOAD_FOLDER

    @property
    def fhir_package_folders(self):
        return FHIR_FOLDERS + [os.getcwd(), self.download_folder]

    def process(self, config_filename=None, download_folder=None):
        config_filename = config_filename or FHIR_EXTRACT_CONFIG_FILENAME
        self.download_folder = download_folder or FHIR_PACKAGE_DOWNLOAD_FOLDER

        if not os.path.exists(config_filename):
            raise FilePathNotExists(f"FHIR extractor config file '{config_filename}' not found.")

        with open(config_filename, 'r') as _file:
            extract_config = yaml.safe_load(_file)

        output_folder = extract_config['output']
        self._prepare_output_folder(output_folder)

        packages = extract_config['packages']
        
        for package_name, resources in packages.items():
            version = resources['version']
            resource_list = resources['resources']
            
            package_folder = self._ensure_package_downloaded(package_name, version)
            
            for resource in resource_list:
                self._process_resource(package_folder, resource, output_folder)

    def _prepare_output_folder(self, output_folder):
        if os.path.exists(output_folder):
            shutil.rmtree(output_folder)
        os.makedirs(output_folder, exist_ok=True)

    def _ensure_package_downloaded(self, package_name, version):
        for fhir_folder in self.fhir_package_folders:
            package_folder = os.path.join(fhir_folder, f"{package_name}#{version}", "package")
            if os.path.exists(package_folder):
                return package_folder

        package_url = f"{FHIR_PACKAGE_REGISTRY_URL}/{package_name}/{version}"
        response = requests.get(package_url, stream=True)
        if response.status_code == 200:
            package_tgz_path = os.path.join(self.download_folder, f"{package_name}#{version}.tgz")
            os.makedirs(os.path.dirname(package_tgz_path), exist_ok=True)
            with open(package_tgz_path, "wb") as f:
                shutil.copyfileobj(response.raw, f)

            try:
                with tarfile.open(package_tgz_path, 'r:gz') as tar_ref:
                    extract_path = os.path.join(self.download_folder, f"{package_name}#{version}")
                    tar_ref.extractall(extract_path)
                os.remove(package_tgz_path)
                return os.path.join(extract_path, "package")
            except tarfile.TarError:
                os.remove(package_tgz_path)
                raise FileFormatException(f"Downloaded file for package {package_name}#{version} is not a valid TAR.GZ archive.")
        else:
            raise DownloadException(f"Failed to download package {package_name}#{version} from {FHIR_PACKAGE_REGISTRY_URL}. Status code: {response.status_code}")

    def _process_resource(self, package_folder, resource, output_folder):
        resource_type, resource_id = resource.split('/')
        possible_filenames = self._generate_possible_filenames(resource_type, resource_id)

        for resource_filename in possible_filenames:
            resource_path = os.path.join(package_folder, resource_filename)
            if os.path.exists(resource_path):
                self._copy_resource(resource_path, output_folder)
                return

        cli.print_command(f"Resource {resource_type}/{resource_id} not found in package {package_folder}")

    def _generate_possible_filenames(self, resource_type, resource_id):
        return [
            f"{resource_type}-{resource_id}.json",
            f"{resource_id}.{resource_type}.json",
            f"{resource_type}-{resource_id}.xml",
            f"{resource_id}.{resource_type}.xml",
            os.path.join(resource_type, f"{resource_id}.xml"),
            os.path.join(resource_type, f"{resource_id}.json"),
            os.path.join('examples', f"{resource_type}-{resource_id}.json"),
            os.path.join('examples', f"{resource_id}.{resource_type}.json"),
            os.path.join('examples', f"{resource_type}-{resource_id}.xml"),
            os.path.join('examples', f"{resource_id}.{resource_type}.xml"),
        ]

    def _copy_resource(self, resource_path, output_folder):
        target_path = os.path.join(output_folder, os.path.basename(resource_path))
        shutil.copy(resource_path, target_path)
        cli.print_command(f"Copied {os.path.basename(resource_path)} to {target_path}")
