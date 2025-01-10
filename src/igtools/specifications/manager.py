import os
import yaml
import warnings

from datetime import datetime
from bs4 import BeautifulSoup

from ..utils import id
from .data import Release, State, Requirement


warnings.simplefilter("ignore")


class ReleaseManager(object):

    def __init__(self, config):
        self.config = config

    @property
    def directory(self):
        return os.path.join(self.config.path, "releases")

    def load(self):
        return self.load_version(version=self.config.current)

    def load_version(self, version):
        release = Release(
            name=self.config.name,
            version=version
        )
        if not version:
            return release

        release.requirements = self.load_requirement(path=self.release_directory(version=version))
        release.archive = self.load_requirement(path=self.archive_directory())
        return release
    
    def load_requirement(self, path):
        requirements = []
        if os.path.exists(path):
            for file_name in os.listdir(path):
                if file_name.endswith('.yaml'):
                    file_path = os.path.join(path, file_name)
                    with open(file_path, 'r', encoding='utf-8') as file:
                        requirements.append(Requirement().deserialize(data=yaml.safe_load(file)))
        return requirements

    def save(self, release):
        release_dir = self.release_directory(version=release.version)

        # Ensure the directory exists
        if not os.path.exists(release_dir):
            os.makedirs(release_dir)

        for requirement in release.requirements:
            file_name = f"{requirement.id}.yaml"
            file_path = os.path.join(release_dir, file_name)
            with open(file_path, 'w', encoding='utf-8') as file:
                yaml.dump(requirement.serialize(), file, default_flow_style=False, allow_unicode=True)

    def archive(self, requirements):
        archive_dir = self.archive_directory()
        if not os.path.exists(archive_dir):
            os.makedirs(archive_dir)
        for requirement in requirements:
            file_name = f"{requirement.id}.yaml"
            file_path = os.path.join(archive_dir, file_name)
            with open(file_path, 'w', encoding='utf-8') as file:
                yaml.dump(requirement.serialize(), file, default_flow_style=False, allow_unicode=True)

    def archive_directory(self):
        return os.path.join(self.directory, 'archive')

    def release_directory(self, version):
        return os.path.join(self.directory, version.replace('.', '_'))

    def create(self, version, force=False):
        release_dir = self.release_directory(version=version)

        if os.path.exists(release_dir) and not force:
            raise FileExistsError(f"Release version {version} already exists.")

        release = self.load()
        stable_requirements = []
        archive_requirements = []
        if release.version != version:
            for req in release.requirements:
                if req.status == State.DELETED.value:
                    archive_requirements.append(req)
                else:
                    req.status = State.STABLE.value
                    stable_requirements.append(req)
            release.version = version
            release.requirements = stable_requirements

        self.save(release)
        self.archive(archive_requirements)

        # Update config to reflect the new current version
        self.config.current = version
        self.config.add_release(version=version)
        self.config.save()


class Processor(object):

    def __init__(self, config, input=None):
        self.config = config
        self.release_manager = ReleaseManager(config=self.config)
        self.input_path = input or self.config.directory

    def is_process_file(self, file):
        return file.endswith('.html') or file.endswith('.md')

    def check(self):
        if not self.config.current:
            raise Exception('TODO: Custom Exception for no version set.')
        if not os.path.exists(self.release_manager.release_directory(version=self.config.current)):
            raise FileExistsError(f"Release version {self.config.current} not exists.")
        
        release = self.release_manager.load()
        seen_ids = set()

        for req in release.archive:
            id.add_id(id=req.id)
            seen_ids.add(req.id)

        for req in release.requirements:
            if req.id not in seen_ids:
                seen_ids.add(req.id)
            else:
                raise ValueError(f"Duplicate ID detected in file {req.source}: {req.id}")

        for root, _, files in os.walk(self.input_path):
            for file in files:
                if self.is_process_file(file=file):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r+', encoding='utf-8') as file:
                        content = file.read()
                        soup = BeautifulSoup(content, 'html.parser')
                    for req in soup.find_all('requirement'):
                        if req.has_attr('id'):
                            req_id = req['id']
                            if id.is_already_added(id=req_id):
                                raise ValueError(f"Duplicate ID detected in file {file_path}: {req_id}")
                            id.add_id(id=req_id)

    def process(self):
        self.check()
        requirements = []
        release = self.release_manager.load()
        for req in release.requirements + release.archive:
            if not id.is_already_added(id=req.id):
                id.add_id(id=req.id)
        existing_map = {req.id: req for req in release.requirements}

        for root, _, files in os.walk(self.input_path):
            for file in files:
                if file.endswith('.html') or file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    reqs = self.process_file(file_path, existing_map)
                    requirements.extend(reqs)

        # Detect duplicate IDs
        seen_ids = set()
        for req in requirements:
            if req.id in seen_ids:
                raise ValueError(f"Duplicate ID detected in file {req.source}: {req.id}")
            seen_ids.add(req.id)

        # Detect removed requirements
        existing_ids = set(existing_map.keys())
        new_ids = {req.id for req in requirements}
        removed_ids = existing_ids - new_ids

        for removed_id in removed_ids:
            removed_req = existing_map[removed_id]
            if removed_req.status != State.NEW.value and removed_req.status != State.DELETED.value:
                if removed_req.status != State.STABLE.value:
                    removed_req.version += 1
                removed_req.status = State.DELETED.value
                removed_req.deleted = datetime.now()
                requirements.append(removed_req)

        # Save
        self.config.save()
        
        release.requirements = requirements
        self.release_manager.save(release=release)


    def process_file(self, file_path, existing_map):
        with open(file_path, 'r+', encoding='utf-8') as file:
            content = file.read()
            soup = BeautifulSoup(content, 'html.parser')

        modified = False
        requirements = []
        
        for soup_req in soup.find_all('requirement'):
            if not soup_req.has_attr('id'):
                req_id = id.generate_id(prefix=f"{self.config.prefix}{self.config.separator}")
                soup_req['id'] = req_id
                id.add_id(req_id)
                modified = True
            else:
                req_id = soup_req['id']
            
            text = soup_req.decode_contents().strip()
            title = soup_req.get('title', "") #.encode('unicode_escape').decode('utf-8')
            target = soup_req.get('target', "") #.encode('unicode_escape').decode('utf-8')

            # Check for updates
            if req_id in existing_map:
                existing_req = existing_map[req_id]

                if existing_req.text != text or existing_req.title != title or existing_req.target != target:
                    existing_req.text = text
                    existing_req.title = title
                    existing_req.target = target
                    if existing_req.status != State.NEW.value:
                        if existing_req.status == State.STABLE.value:
                            existing_req.version += 1
                        existing_req.status = State.MODIFIED.value
                        soup_req['version'] = str(existing_req.version)
                    modified = True
                    existing_req.modified = datetime.now()
                elif existing_req.status == State.DELETED.value:
                    existing_req.status = State.MODIFIED.value
                    existing_req.modified = datetime.now()
                    existing_req.deleted = None
                elif existing_req.source != file_path:
                    if existing_req.status != State.NEW.value:
                        if existing_req.status == State.STABLE.value:
                            existing_req.version += 1
                        existing_req.status = State.MOVED.value
                        existing_req.modified = datetime.now()
                    existing_req.source = file_path
                else:
                    soup_req['version'] = str(existing_req.version)
                requirements.append(existing_req)
            else:
                new_req = Requirement()
                new_req.id = req_id
                new_req.text = text
                new_req.title = title
                new_req.target = target
                new_req.source = file_path
                new_req.version = 1
                new_req.status = State.NEW.value
                new_req.created = datetime.now()
                new_req.modified = datetime.now()
                soup_req['version'] = "1"
                requirements.append(new_req)
                modified = True

        if modified:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(str(soup))

        return requirements
