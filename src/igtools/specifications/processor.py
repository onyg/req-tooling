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

TRUE_VALUES = ["true", "True", "TRUE", "1"]


class Processor:
    def __init__(self, config, input=None):
        self.config = config
        self.release_manager = release.ReleaseManager(config)
        self._clean_up = False
        self.dry_run = False
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

    def all_filepaths(self):
        file_paths = []
        for root, _, files in os.walk(self.input_path):
            for file in filter(self.is_process_file, files):
                file_paths.append(os.path.join(root, file))
        return file_paths

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

        for file_path in self.all_filepaths():
            with open(file_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')

            for soup_req in soup.find_all('requirement'):
                if soup_req.has_attr('key'):
                    req_key = soup_req['key']
                    if req_key and req_key in seen_keys:
                        raise DuplicateRequirementIDException(f"Duplicate ID detected in file {file_path}: {req_key}")
                    seen_keys.add(req_key)

    def process(self):
        release = self.release_manager.load()
        
        if self.release_manager.is_current_release_frozen():
            requirements = self.process_requirements_from_files(release=release, dry_run=True)
            self.release_manager.verify_release_integrity(requirements=requirements)
            return
        self.check()

        requirements = self.process_requirements_from_files(release=release, dry_run=False)

        self.config.save()
        release.requirements = requirements
        self.release_manager.save(release)

    def process_requirements_from_files(self, release, dry_run=False):
        existing_map = {req.key: req for req in release.requirements}
        requirements = self._process_files(existing_map, dry_run=dry_run)
        self._detect_removed_requirements(requirements, existing_map)
        return requirements

    def _process_files(self, existing_map, dry_run=False):
        requirements = []

        for file_path in self.all_filepaths():
            requirements.extend(FileProcessor(processor=self, file_path=file_path, existing_map=existing_map).process(dry_run=dry_run))
        
        return requirements

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

    def reset_all_meta_tags(self):
        for file_path in self.all_filepaths():
            ResetMetaTagsHelper(file_path=file_path).reset()


class FileProcessor:

    # regex for the <requirement> tag
    REQUIREMENT_PATTERN = re.compile(r'(<requirement\b[^>]*)(>.*?</requirement>)', re.DOTALL)
    # tags to be stripped from the inner text
    ACTOR_PATTERN = re.compile(r"<actor\b[^>]*/>|<actor\b[^>]*>.*?</actor>", re.IGNORECASE | re.DOTALL)
    META_PATTERN = re.compile(r"<meta\b[^>]*/>|<meta\b[^>]*>.*?</meta>",   re.IGNORECASE | re.DOTALL)


    def __init__(self, processor, file_path, existing_map):
        self.processor = processor
        self.file_path = file_path
        self.existing_map = existing_map
        self.modified = False
        self.requirements = []

    def process(self, dry_run=False):
        with open(self.file_path, 'r', encoding='utf-8') as file:
            original = file.read()

        self.modified = False
        self.requirements = []

        # Replace only the start requirement tag
        updated_html = self.REQUIREMENT_PATTERN.sub(self._update_match, original)

        if self.modified and not dry_run:
            with open(self.file_path, 'w', encoding='utf-8') as file:
                file.write(updated_html)

        return self.requirements

    def update_existing_requirement(self, req, text, title, actor, conformance, test_procedures, meta=None):
        _now = datetime.now()
        actor = utils.to_list(actor)
        req.actor = utils.to_list(req.actor)
        fp, _ = normalize.build_fingerprint(text=text,
                                            title=title,
                                            conformance=conformance,
                                            actors=actor,
                                            test_procedures=test_procedures)

        is_modified = req.content_hash != fp
        if is_modified:
            req.text = utils.clean_text(text)
            req.title = title
            req.conformance = conformance
            req.content_hash = fp
        elif req.text != text:
            req.text = utils.clean_text(text)

        lock_version = False
        if meta:
            lock_version = meta.get("lockversion", None) in TRUE_VALUES

        if is_modified:
            if not lock_version:
                if req.is_stable:
                    req.version += 1
                if not req.is_new:
                    req.is_modified = True
                req.modified = _now
            req.deleted = None
            req.date = _now

        if req.actor != actor:
            req.actor = actor
            req.modified = _now
        if req.test_procedures != test_procedures:
            req.test_procedures = test_procedures
            req.date = _now

        if req.source != self.file_path:
            req.source = self.file_path
            req.modified = _now
            req.date = _now
            if req.is_stable:
                req.is_moved = True
            elif req.is_deleted:
                req.is_deleted = True
                req.deleted = None
        
        if req.is_deleted:
            req.is_modified = True
            req.deleted = None
        
        return req

    def create_new_requirement(self, req_key, text, title, actor, conformance, test_procedures):
        actor = utils.to_list(actor)
        req = Requirement(
            key=req_key,
            text=text,
            title=title,
            actor=actor,
            source=self.file_path,
            version=0,
            conformance=conformance,
            test_procedures=test_procedures
        )
        req.is_new = True
        req.created = datetime.now()
        req.modified = datetime.now()
        req.date = datetime.now()
        return req

    def _update_match(self, match: re.Match) -> str:
        # nonlocal modified
        start_tag, rest_of_tag = match.groups()

        # Get the data from the xml tag
        soup = BeautifulSoup(match.group(0), 'html.parser')
        requirement_tag = soup.requirement  # Der gefundene <requirement>-Tag

        inner_text = rest_of_tag[len(">"):-len("</requirement>")].strip()
        inner_text = self.ACTOR_PATTERN.sub("", inner_text).strip()
        inner_text = self.META_PATTERN.sub("", inner_text).strip()
        req = self._update_or_create_requirement(requirement_tag, text=inner_text)
        if req:
            self.requirements.append(req)
            # Extract the start tag
            updated_start_tag = str(requirement_tag).split(">", 1)[0]
            updated_requirement = updated_start_tag + rest_of_tag
            if updated_requirement != match.group(0):
                self.modified = True
            return updated_requirement
        # If no modification return original
        return match.group(0)

    def _update_or_create_requirement(self, soup_req, text=None):
        req_key = None
        if soup_req.has_attr('key'):
            req_key = soup_req['key']
        if not req_key:
            req_key = id.generate_id(prefix=f"{self.processor.config.prefix}{self.processor.config.separator}", scope=self.processor.config.scope)
            soup_req['key'] = req_key
            id.add_id(req_key)

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
                    if (tp.get("active") is None or tp.get("active").lower() in TRUE_VALUES)
                ]
                test_procedures[str(actor_tag.get("name"))] = sorted(set(test_ids))

        if len(test_procedures) == 0:
            for actor in utils.to_list(actors):
                test_procedures[str(actor)] = []
        conformance = soup_req.get('conformance', "")

        meta = {"locakversion": False}
        if len(soup_req.find_all("meta")) > 0:
            for _meta in soup_req.find_all("meta"):
                if _meta.has_attr("lockversion"):
                    meta["lockversion"] = _meta.get("lockversion")

        req = None
        if req_key in self.existing_map:
            existing_req = self.existing_map[req_key]
            req = self.update_existing_requirement(existing_req, text, title, actors, conformance, test_procedures, meta=meta)
        else:
            req = self.create_new_requirement(req_key, text, title, actors, conformance, test_procedures)
        if req:
            soup_req['version'] = req.version
        
        return req

                
class ResetMetaTagsHelper:

    LOCKVERSION_ATTR_PATTERN = re.compile(
        r'(\blockversion\b\s*=\s*)(?P<q>["\']?)(?P<val>[^"\'>\s]*)(?P=q)',
        re.IGNORECASE
    )

    def __init__(self, file_path):
        self.file_path = file_path
        self.modified = False

    def replace_lock_attr_in_meta(self, meta_match: re.Match) -> str:
        # Replaces the lockVersion/lockversion attribute value within a single <meta> tag.
        tag = meta_match.group(0)


        def _repl(m: re.Match) -> str:
            # Preserve quotes if present
            q = m.group('q') or ''
            return f"{m.group(1)}{q}false{q}"

        new_tag, count = self.LOCKVERSION_ATTR_PATTERN.subn(_repl, tag, count=1)
        if count > 0 and new_tag != tag:
            self.modified = True
        return new_tag

    def update_match(self, req_match: re.Match) -> str:
        ####
        # Updates a <requirement> block:
        #   - start_tag: the opening <requirement ...>
        #   - rest_of_tag: everything up to and including </requirement>
        # Only <meta> tags inside the requirement block are modified.
        ####
        start_tag, rest_of_tag = req_match.groups()
        updated_rest = FileProcessor.META_PATTERN.sub(self.replace_lock_attr_in_meta, rest_of_tag)
        return start_tag + updated_rest

    def reset(self):
        with open(self.file_path, 'r', encoding='utf-8') as file:
            original = file.read()
        self.modified = False

        updated = FileProcessor.REQUIREMENT_PATTERN.sub(self.update_match, original)

        if self.modified:
            with open(self.file_path, 'w', encoding='utf-8') as file:
                file.write(updated)

