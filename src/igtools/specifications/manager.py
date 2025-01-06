import os
# import json
import yaml

from bs4 import BeautifulSoup

from .data import Release, State, Requirement


class ReleaseManager(object):

    def __init__(self, config):
        self.config = config

    def load(self):
        return self.load_version(version=self.config.current)
        
    def load_version(self, version):
        _release = Release(
                    name=self.config.name,
                    version=version)
        if not version:
            return _release
        input_file = self.get_release_filepath(version=version)
        if not os.path.exists(input_file):
            return _release
        with open(input_file, 'r', encoding='utf-8') as file:
            return _release.deserialize(data=yaml.safe_load(file))
        
    def save(self, release):
        release_file = self.get_release_filepath(version=release.version)
        with open(release_file, 'w', encoding='utf-8') as file:
            yaml.dump(release.serialize(), file, default_flow_style=False, allow_unicode=True)
        
    def get_filepath(self):
        return os.path.join(self.config.path, "releases")
        
    def get_release_filepath(self, version):
        # return os.path.join(self.get_filepath(), f"release_{version.replace('.', '_')}.json")
        return os.path.join(self.get_filepath(), f"release_{version.replace('.', '_')}.yaml")

    def create(self, version):
        if not os.path.exists(self.get_filepath()):
            os.makedirs(self.get_filepath())

        release_file = self.get_release_filepath(version=version)
        if os.path.exists(release_file):
            raise FileExistsError(f"Release version {version} already exists.")
        
        release = self.load()
        stable_requirements = []
        if release.version != version:
            for req in release.requirements:
                if req.status == State.DELETED.value:
                    continue
                req.status = State.STABLE.value
                stable_requirements.append(req)
            release.version = version
            release.requirements = stable_requirements

        self.save(release)
        
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
        if not os.path.exists(self.release_manager.get_release_filepath(version=self.config.current)):
            raise FileExistsError(f"Release version {self.config.current} not exists.")
        current_ids = []
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
                            if req_id in current_ids:
                                raise ValueError(f"Duplicate ID detected in file {file_path}: {req_id}")
                            try:
                                int(req_id.split(str(self.config.separator))[1])
                            except ValueError:
                                raise ValueError(f"Wrong ID format {file_path}: {req_id}")
                            current_ids.append(req_id)
        if current_ids:
            highest_id = max(int(req.split(str(self.config.separator))[1]) for req in current_ids)
            return highest_id
        return 0

    def process(self, reset=False):
        current_max_id = self.check()
        if reset:
            self.config.max_id = current_max_id
        elif current_max_id > self.config.max_id:
            raise Exception(f"TODO: Custom Exception for wrong max id in the config file. Config max id is {self.config.max_id} current is {current_max_id}")
        requirements = []
        release = self.release_manager.load()
        existing_requirements = release.requirements
        current_ids = {req.id for req in existing_requirements}
        existing_map = {req.id: req for req in existing_requirements}

        for root, _, files in os.walk(self.input_path):
            for file in files:
                if file.endswith('.html') or file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    reqs, current_max_id = self.process_file(file_path, current_max_id, current_ids, existing_map)
                    requirements.extend(reqs)

        # Detect duplicate IDs
        seen_ids = set()
        for req in requirements:
            if req.id in seen_ids:
                raise ValueError(f"Duplicate ID detected: {req.id}")
            seen_ids.add(req.id)

        # Detect removed requirements
        existing_ids = set(existing_map.keys())
        new_ids = {req.id for req in requirements}
        removed_ids = existing_ids - new_ids

        for removed_id in removed_ids:
            removed_req = existing_map[removed_id]
            if removed_req.status != State.NEW.value:
                removed_req.version += 1
                removed_req.status = State.DELETED.value
                requirements.append(removed_req)

        # Save
        self.config.max_id = current_max_id
        self.config.save()
        
        release.requirements = requirements
        self.release_manager.save(release=release)


    def process_file(self, file_path, current_max_id, current_ids, existing_map):
        with open(file_path, 'r+', encoding='utf-8') as file:
            content = file.read()
            soup = BeautifulSoup(content, 'html.parser')

        modified = False
        requirements = []
        
        for soup_req in soup.find_all('requirement'):
            if not soup_req.has_attr('id'):
                current_max_id += 1
                req_id = f"{self.config.prefix}{self.config.separator}{current_max_id:05d}"
                soup_req['id'] = req_id
                current_ids.add(req_id)
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
                        if existing_req.status != State.DELETED.value:
                            existing_req.version += 1
                        existing_req.status = State.CHANGE.value
                        soup_req['version'] = str(existing_req.version)
                    modified = True
                elif existing_req.status == State.DELETED.value:
                    existing_req.status = State.CHANGE.value
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
                soup_req['version'] = "1"
                requirements.append(new_req)
                modified = True

        if modified:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(str(soup))

        return requirements, current_max_id
