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
from . import normalize
from . import release


warnings.simplefilter("ignore")


class Processor:
    def __init__(self, config, input=None):
        self.config = config
        self.release_manager = release.ReleaseManager(config)
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
        if self.release_manager.check_final():
            raise FinalReleaseException()
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
        actor_pattern = re.compile(r"<actor\b[^>]*>.*?</actor>", re.DOTALL | re.IGNORECASE)

        def update_match(match):
            nonlocal modified
            start_tag, rest_of_tag = match.groups()

            # Get the data from the xml tag
            soup = BeautifulSoup(match.group(0), 'html.parser')
            requirement_tag = soup.requirement  # Der gefundene <requirement>-Tag

            inner_text = rest_of_tag[len(">"):-len("</requirement>")].strip()
            inner_text = actor_pattern.sub("", inner_text).strip()
            req = self._update_or_create_requirement(requirement_tag, existing_map, file_path, text=inner_text)
            if req:
                requirements.append(req)
                # Extract the start tag
                updated_start_tag = str(requirement_tag).split(">", 1)[0]
                updated_requirement = updated_start_tag + rest_of_tag
                if updated_requirement != match.group(0):
                    modified = True
                return updated_requirement
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

        actors = soup_req.get('actor', "")
        test_procedures = {}

        if len(soup_req.find_all("actor")) > 0:
            actors = []
            for actor_tag in soup_req.find_all("actor"):
                actors.append(actor_tag.get("name"))
                test_ids = [
                    tp.get("id")
                    for tp in actor_tag.find_all("testprocedure")
                    if (tp.get("active") is None or tp.get("active").lower() in ("true", "1"))
                ]
                test_procedures[str(actor_tag.get("name"))] = sorted(set(test_ids))

        if len(test_procedures) == 0:
            for actor in utils.to_list(actors):
                test_procedures[str(actor)] = []
        conformance = soup_req.get('conformance', "")

        req = None
        if req_key in existing_map:
            existing_req = existing_map[req_key]
            req = self.update_existing_requirement(existing_req, text, title, actors, file_path, conformance, test_procedures)
        else:
            req = self.create_new_requirement(req_key, text, title, actors, file_path, conformance, test_procedures)
        if req:
            soup_req['version'] = req.version
        
        return req

    @classmethod
    def update_existing_requirement(cls, req, text, title, actor, file_path, conformance, test_procedures):
        actor = utils.to_list(actor)
        req.actor = utils.to_list(req.actor)
        fp_req, _ = normalize.build_requirement_fingerprint(req)
        fp, _ = normalize.build_fingerprint(text=text,
                                         title=title,
                                         conformance=conformance,
                                         actors=actor,
                                         test_procedures=test_procedures)

        is_modified = fp_req != fp
        if is_modified:
            req.text = utils.clean_text(text)
            req.title = title
            req.conformance = conformance
            req.actor = actor
            req.test_procedures = test_procedures
        elif req.text != text:
            req.text = utils.clean_text(text)
        
        if is_modified:
            if req.is_stable:
                req.version += 1
            if not req.is_new:
                req.is_modified = True
            req.modified = datetime.now()
            req.deleted = None
            req.date = datetime.now()

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
    def create_new_requirement(cls, req_key, text, title, actor, file_path, conformance, test_procedures):
        actor = utils.to_list(actor)
        req = Requirement(
            key=req_key,
            text=text,
            title=title,
            actor=actor,
            source=file_path,
            version=0,
            conformance=conformance,
            test_procedures=test_procedures
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
