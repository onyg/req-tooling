import os
import yaml
import warnings
from datetime import datetime
from bs4 import BeautifulSoup
from ..utils import id
from .data import Release, Requirement
from ..errors import (NoReleaseVersionSetException, 
                      ReleaseNotFoundException, 
                      ReleaseAlreadyExistsException, 
                      DuplicateRequirementIDException,
                      FinalReleaseException)

warnings.simplefilter("ignore")

class ReleaseManager:
    def __init__(self, config):
        self.config = config

    @property
    def directory(self):
        return os.path.join(self.config.path, "releases")

    def load(self):
        return self.load_version(self.config.current)

    def load_version(self, version):
        release = Release(name=self.config.name, version=version)

        if not version:
            return release

        release.requirements = self._load_requirements(self.release_directory(version))
        release.archive = self._load_requirements(self.archive_directory())
        return release

    def _load_requirements(self, path):
        if not os.path.exists(path):
            return []

        requirements = []
        for file_name in filter(lambda f: f.endswith('.yaml'), os.listdir(path)):
            with open(os.path.join(path, file_name), 'r', encoding='utf-8') as file:
                requirements.append(Requirement().deserialize(yaml.safe_load(file)))
        return requirements

    def save(self, release):
        release_dir = self.release_directory(release.version)
        os.makedirs(release_dir, exist_ok=True)

        for requirement in release.requirements:
            if requirement.for_deletion:
                self._delete_requirement(requirement=requirement, directory=release_dir)
            else:
                self._save_requirement(requirement=requirement, directory=release_dir)

    def _delete_requirement(self, requirement, directory):
        file_path = os.path.join(directory, f"{requirement.id}.yaml")
        if os.path.exists(file_path):
            os.remove(file_path)

    def _save_requirement(self, requirement, directory):
        file_path = os.path.join(directory, f"{requirement.id}.yaml")
        with open(file_path, 'w', encoding='utf-8') as file:
            yaml.dump(requirement.serialize(), file, default_flow_style=False, allow_unicode=True)

    def archive(self, requirements):
        archive_dir = self.archive_directory()
        os.makedirs(archive_dir, exist_ok=True)

        for requirement in requirements:
            self._save_requirement(requirement, archive_dir)

    def archive_directory(self):
        return os.path.join(self.directory, 'archive')

    def release_directory(self, version):
        return os.path.join(self.directory, version.replace('.', '_'))
    
    def check_new_version(self, version, force=False):
        release_dir = self.release_directory(version)
        if os.path.exists(release_dir) and not force:
            raise ReleaseAlreadyExistsException(f"Release version {version} already exists.")
        return True

    def create(self, version, force=False):
        self.check_new_version(version=version, force=force)

        release = self.load()
        stable_requirements, archive_requirements = self._categorize_requirements(release, version)

        self.save(release)
        self.archive(archive_requirements)

        self.config.current = version
        self.config.add_release(version)
        self.config.save()

    def _categorize_requirements(self, release, version):
        stable_requirements, archive_requirements = [], []

        if release.version != version:
            for req in release.requirements:
                if req.is_deleted:
                    archive_requirements.append(req)
                else:
                    req.is_stable = True
                    stable_requirements.append(req)

            release.version = version
            release.requirements = stable_requirements

        return stable_requirements, archive_requirements
    
    def set_current_as_final(self):
        if self.config.current is None:
            raise NoReleaseVersionSetException()
        elif not os.path.exists(self.release_directory(self.config.current)):
            raise ReleaseNotFoundException(f"Release version {self.config.current} does not exist.")
        self.config.final = self.config.current
        self.config.save()

    def is_current_final(self):
        return self.config.current == self.config.final

    def check_final(self):
        if self.is_current_final():
            raise FinalReleaseException()

class Processor:
    def __init__(self, config, input=None):
        self.config = config
        self.release_manager = ReleaseManager(config)
        self.input_path = input or config.directory

    def is_process_file(self, file):
        return file.endswith(('.html', '.md'))

    def check(self):
        if not self.config.current:
            raise NoReleaseVersionSetException()

        if not os.path.exists(self.release_manager.release_directory(self.config.current)):
            raise ReleaseNotFoundException(f"Release version {self.config.current} does not exist.")

        self._validate_requirements()
        self._validate_input_files()

    def _validate_requirements(self):
        release = self.release_manager.load()
        seen_ids = set()

        for req in release.archive + release.requirements:
            if req.id in seen_ids:
                raise DuplicateRequirementIDException(f"Duplicate ID detected: {req.id} in file {req.source}")
            seen_ids.add(req.id)

    def _validate_input_files(self):
        seen_ids = set()
        release = self.release_manager.load()

        for req in release.archive:
            seen_ids.add(req.id)

        for root, _, files in os.walk(self.input_path):
            for file in filter(self.is_process_file, files):
                file_path = os.path.join(root, file)

                with open(file_path, 'r', encoding='utf-8') as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')

                for soup_req in soup.find_all('requirement'):
                    if soup_req.has_attr('id'):
                        req_id = soup_req['id']
                        if req_id in seen_ids:
                            raise DuplicateRequirementIDException(f"Duplicate ID detected in file {file_path}: {req_id}")
                        seen_ids.add(req_id)

    def process(self):
        self.release_manager.check_final()
        self.check()

        release = self.release_manager.load()
        existing_map = {req.id: req for req in release.requirements}
        requirements = self._process_files(existing_map)

        self._detect_removed_requirements(requirements, existing_map)

        self.config.save()
        release.requirements = requirements
        self.release_manager.save(release)

    def _process_files(self, existing_map):
        requirements = []

        for root, _, files in os.walk(self.input_path):
            for file in filter(self.is_process_file, files):
                file_path = os.path.join(root, file)
                requirements.extend(self._process_file(file_path, existing_map))

        return requirements

    def _process_file(self, file_path, existing_map):
        with open(file_path, 'r+', encoding='utf-8') as file:
            soup = BeautifulSoup(file.read(), 'html.parser')

        modified = False
        requirements = []

        for soup_req in soup.find_all('requirement'):
            req = self._update_or_create_requirement(soup_req, existing_map, file_path)
            if req:
                requirements.append(req)
                modified = True
                # TODO: On each run, modified is set to True, which saves the file even though nothing has changed 
                # modified = not req.is_stable and not req.is_deleted and not req.for_deletion

        if modified:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(str(soup))

        return requirements

    def _update_or_create_requirement(self, soup_req, existing_map, file_path):
        if not soup_req.has_attr('id'):
            req_id = id.generate_id(prefix=f"{self.config.prefix}{self.config.separator}", suffix="1")
            soup_req['id'] = req_id
            id.add_id(req_id)
        else:
            req_id = soup_req['id']

        text = soup_req.decode_contents().strip()
        title = soup_req.get('title', "")
        target = soup_req.get('target', "")

        req = None
        if req_id in existing_map:
            existing_req = existing_map[req_id]
            req = self._update_existing_requirement(existing_req, text, title, target, file_path)
        else:
            req = self._create_new_requirement(req_id, text, title, target, file_path)
        if req:
            soup_req['version'] = req.version
        
        return req

    def _update_existing_requirement(self, req, text, title, target, file_path):
        if (req.text, req.title, req.target) != (text, title, target):
            req.text, req.title, req.target = text, title, target
            if req.is_stable:
                req.version += 1
            if not req.is_new:
                req.is_modified = True
            req.modified = datetime.now()
            req.deleted = None
        
        if req.source != file_path:
            req.source = file_path
            req.modified = datetime.now()
            if req.is_stable:
                req.is_moved = True
            elif req.is_deleted:
                req.is_deleted = True
                req.deleted = None
        
        if req.is_deleted:
            req.is_modified = True
            req.deleted = None
        
        return req

    def _create_new_requirement(self, req_id, text, title, target, file_path):
        req = Requirement(
            id=req_id,
            text=text,
            title=title,
            target=target,
            source=file_path,
            version=1
        )
        req.is_new = True
        req.created = datetime.now()
        req.modified = datetime.now()
        return req

    def _detect_removed_requirements(self, requirements, existing_map):
        existing_ids = set(existing_map.keys())
        new_ids = {req.id for req in requirements}
        removed_ids = existing_ids - new_ids
        for removed_id in removed_ids:
            removed_req = existing_map[removed_id]
            if removed_req.is_new:
                removed_req.for_deletion = True
            else:
                removed_req.is_deleted = True
            removed_req.deleted = datetime.now()
            requirements.append(removed_req)
            # if not removed_req.is_new:
            #     removed_req.is_deleted = True
            #     removed_req.deleted = datetime.now()
            #     requirements.append(removed_req)
            # elif removed_req.is_new:
            #     removed_req.is_new_deleted = True
            #     requirements.append(removed_req)
