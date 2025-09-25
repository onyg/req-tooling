import os
import re
import yaml
import warnings
from datetime import datetime
from bs4 import BeautifulSoup
from ..utils import id, utils
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
        if version not in self.config.releases:
            raise ReleaseNotFoundException(f"Release version {version} does not exist.")
        release = Release(name=self.config.name, version=version)

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
                self.delete_requirement(requirement=requirement, directory=release_dir)
            else:
                self.save_requirement(requirement=requirement, directory=release_dir)

    def delete_requirement(self, requirement, directory):
        file_path = os.path.join(directory, f"{requirement.key}.yaml")
        if os.path.exists(file_path):
            os.remove(file_path)

    def save_requirement(self, requirement, directory):
        file_path = os.path.join(directory, f"{requirement.key}.yaml")
        with open(file_path, 'w', encoding='utf-8') as file:
            yaml.dump(requirement.serialize(), file, default_flow_style=False, allow_unicode=True)

    def archive(self, requirements):
        archive_dir = self.archive_directory()
        os.makedirs(archive_dir, exist_ok=True)

        for requirement in requirements:
            self.save_requirement(requirement, archive_dir)

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

        if self.config.current is None:
            release = Release(name=self.config.name, version=version)
        else:
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
        if self.config.final is None:
            return False
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
        seen_keys = set()

        for req in release.archive + release.requirements:
            if req.key in seen_keys:
                raise DuplicateRequirementIDException(f"Duplicate KEY detected: {req.key} in file {req.source}")
            seen_keys.add(req.key)

    def _validate_input_files(self):
        seen_keys = set()
        release = self.release_manager.load()

        for req in release.archive:
            seen_keys.add(req.key)

        for root, _, files in os.walk(self.input_path):
            for file in filter(self.is_process_file, files):
                file_path = os.path.join(root, file)

                with open(file_path, 'r', encoding='utf-8') as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')

                for soup_req in soup.find_all('requirement'):
                    if soup_req.has_attr('key'):
                        req_key = soup_req['key']
                        if req_key in seen_keys:
                            raise DuplicateRequirementIDException(f"Duplicate ID detected in file {file_path}: {req_key}")
                        seen_keys.add(req_key)

    def process(self):
        self.release_manager.check_final()
        self.check()

        release = self.release_manager.load()
        existing_map = {req.key: req for req in release.requirements}
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
        with open(file_path, 'r', encoding='utf-8') as file:
            original = file.read()

        modified = False
        requirements = []

        # regex for the <requirement> tag
        requirement_pattern = re.compile(r'(<requirement\b[^>]*)(>.*?</requirement>)', re.DOTALL)

        def update_match(match):
            nonlocal modified
            start_tag, rest_of_tag = match.groups()

            # Get the data from the xml tag
            soup = BeautifulSoup(match.group(0), 'html.parser')
            requirement_tag = soup.requirement  # Der gefundene <requirement>-Tag

            inner_text = rest_of_tag[len(">"):-len("</requirement>")].strip()
            req = self._update_or_create_requirement(requirement_tag, existing_map, file_path, text=inner_text)
            if req:
                requirements.append(req)
                modified = True
                # TODO: On each run, modified is set to True, which saves the file even though nothing has changed 
                # modified = not req.is_stable and not req.is_deleted and not req.for_deletion

                # Extract the start tag
                updated_start_tag = str(requirement_tag).split(">", 1)[0] 
                # print(updated_start_tag + rest_of_tag)
                return updated_start_tag + rest_of_tag  
            # If no modification return original
            return match.group(0) 

        # Replace only the start requirement tag
        updated_html = requirement_pattern.sub(update_match, original)

        if modified:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(updated_html)

        return requirements

    def _update_or_create_requirement(self, soup_req, existing_map, file_path, text=None):
        if not soup_req.has_attr('key'):
            req_key = id.generate_id(prefix=f"{self.config.prefix}{self.config.separator}", scope=self.config.scope)
            soup_req['key'] = req_key
            id.add_id(req_key)
        else:
            req_key = soup_req['key']

        if text is None:
            text = soup_req.decode_contents().strip()
        title = soup_req.get('title', "")
        actor = soup_req.get('actor', "")
        conformance = soup_req.get('conformance', "")

        req = None
        if req_key in existing_map:
            existing_req = existing_map[req_key]
            req = self.update_existing_requirement(existing_req, text, title, actor, file_path, conformance)
        else:
            req = self.create_new_requirement(req_key, text, title, actor, file_path, conformance)
        if req:
            soup_req['version'] = req.version
        
        return req

    @classmethod
    def update_existing_requirement(cls, req, text, title, actor, file_path, conformance):

        is_modified = False
        if req.text != text:
            if utils.normalize(req.text) != utils.normalize(text):
                is_modified = True
            req.text = utils.clean_text(text)

        if (req.title, req.conformance) != (title, conformance):
            req.text, req.title, req.conformance = text, title, conformance
            is_modified = True

        if is_modified:
            if req.is_stable:
                req.version += 1
            if not req.is_new:
                req.is_modified = True
            req.modified = datetime.now()
            req.deleted = None
            req.date = datetime.now()

        if req.actor != actor:
            req.actor = actor

        if req.source != file_path:
            req.source = file_path
            req.modified = datetime.now()
            req.date = datetime.now()
            if req.is_stable:
                req.is_moved = True
            elif req.is_deleted:
                req.is_deleted = True
                req.deleted = None
        
        if req.is_deleted:
            req.is_modified = True
            req.deleted = None
        
        return req

    @classmethod
    def create_new_requirement(cls, req_key, text, title, actor, file_path, conformance):
        req = Requirement(
            key=req_key,
            text=text,
            title=title,
            actor=actor,
            source=file_path,
            version=0,
            conformance=conformance
        )
        req.is_new = True
        req.created = datetime.now()
        req.modified = datetime.now()
        req.date = datetime.now()
        return req

    def _detect_removed_requirements(self, requirements, existing_map):
        existing_keys = set(existing_map.keys())
        new_keys = {req.key for req in requirements}
        removed_keys = existing_keys - new_keys
        for removed_key in removed_keys:
            removed_req = existing_map[removed_key]

            if removed_req.is_new:
                removed_req.for_deletion = True
                removed_req.deleted = datetime.now()
                removed_req.date = datetime.now()
                requirements.append(removed_req)
                continue

            if not removed_req.is_deleted:
                removed_req.is_deleted = True
                removed_req.deleted = datetime.now()
                removed_req.date = datetime.now()
                requirements.append(removed_req)
            else:
                requirements.append(removed_req)
