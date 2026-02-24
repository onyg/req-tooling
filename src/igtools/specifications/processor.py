import os
import re
import yaml
import warnings
import difflib
from datetime import datetime
from bs4 import BeautifulSoup
from ..utils import id, utils
from .data import Requirement
from ..errors import (NoReleaseVersionSetException, 
                      ReleaseNotFoundException,
                      ReleaseAlreadyExistsException, 
                      DuplicateRequirementIDException,
                      InvalidTestProcedureIDException,
                      FinalReleaseException)
from . import normalize
from . import release


warnings.simplefilter("ignore")

TRUE_VALUES = ["true", "True", "TRUE", "1"]


class Processor:
    def __init__(self, config, input=None, dry_run=False):
        self.config = config
        self.release_manager = release.ReleaseManager(config)
        self._clean_up = False
        self.dry_run = dry_run
        self.input_path = input or config.directory
        self.key_generator = None

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

    def _load_diff_to_releases(self):
        diff_to_releases = []
        if not getattr(self.config, 'diff_to', None):
            return diff_to_releases

        seen_versions = set()
        for version in self.config.diff_to:
            if version == self.config.current or version in seen_versions:
                continue
            seen_versions.add(version)
            diff_to_releases.append(self.release_manager.load_version(version))

        return diff_to_releases

    def _validate_input_files(self, validate_requirement_keys=True):
        seen_keys = set()
        if validate_requirement_keys:
            release = self.release_manager.load()
            for req in release.archive:
                seen_keys.add(req.key)

        try:
            from ..polarion.polarion import load_polarion_mappings
            _, testproc_mapping = load_polarion_mappings()
        except Exception as exc:
            raise InvalidTestProcedureIDException(
                f"Could not load Polarion test procedure mappings: {exc}"
            ) from exc

        errors = []

        for file_path in self.all_filepaths():
            with open(file_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')

            if validate_requirement_keys:
                for soup_req in soup.find_all('requirement'):
                    if soup_req.has_attr('key'):
                        req_key = soup_req['key']
                        if req_key and req_key in seen_keys:
                            raise DuplicateRequirementIDException(f"Duplicate ID detected in file {file_path}: {req_key}")
                        seen_keys.add(req_key)

            for tp_tag in soup.find_all('testprocedure'):
                tp_id = (tp_tag.get('id') or "").strip()
                if not tp_id:
                    errors.append(f"Missing testProcedure id in file {file_path}: {tp_tag}")
                    continue

                if tp_id not in testproc_mapping:
                    errors.append(
                        f"Unknown testProcedure id '{tp_id}' in file {file_path}. "
                        "Add it to src/igtools/mappings/polarion.yaml:testproc_to_id or fix the tag."
                    )

        if errors:
            raise InvalidTestProcedureIDException("\n".join(errors))

    def process(self):
        release = self.release_manager.load()
        diff_to_releases = self._load_diff_to_releases()
        
        if self.release_manager.is_current_release_frozen():
            requirements = self.process_requirements_from_files(
                release=release,
                diff_to_releases=diff_to_releases,
                dry_run=True
            )
            self._validate_input_files(validate_requirement_keys=False)
            requirements = self.process_requirements_from_files(
                release=release,
                diff_to_releases=diff_to_releases,
                dry_run=True
            )
            self.release_manager.verify_release_integrity(requirements=requirements)
            return
        self.check()

        requirements = self.process_requirements_from_files(
            release=release,
            diff_to_releases=diff_to_releases,
            dry_run=self.dry_run
        )


        release.requirements = requirements
        if not self.dry_run:
            self.config.save()
            self.release_manager.save(release)
        return release

    def process_requirements_from_files(self, release, diff_to_releases=None, dry_run=False):
        existing_map = {req.key: req for req in release.requirements}
        diff_to_maps = {}
        if diff_to_releases:
            for diff_release in diff_to_releases:
                diff_to_maps[diff_release.version] = {req.key: req for req in diff_release.requirements}

        self.key_generator = id.create_generator(config=self.config, existing_keys=existing_map.keys())
        requirements = self._process_files(existing_map, diff_to_maps=diff_to_maps, dry_run=dry_run)
        self._detect_removed_requirements(requirements, existing_map)
        return requirements

    def _process_files(self, existing_map, diff_to_maps=None, dry_run=False):
        requirements = []

        for file_path in self.all_filepaths():
            requirements.extend(
                FileProcessor(
                    processor=self,
                    file_path=file_path,
                    existing_map=existing_map,
                    diff_to_maps=diff_to_maps or {}
                ).process(dry_run=dry_run)
            )
        
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
    TEST_PROCEDURE_PATTERN = re.compile(
        r"<testProcedure\b(?P<attrs>[^>]*?)(?:\s*/>|>.*?</testProcedure>)",
        re.IGNORECASE | re.DOTALL
    )

    def __init__(self, processor, file_path, existing_map, diff_to_maps=None):
        self.processor = processor
        self.file_path = file_path
        self.existing_map = existing_map
        self.diff_to_maps = diff_to_maps or {}
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

    def _next_key(self):
        """Generate next requirement key using the key generator"""
        return self.processor.key_generator.generate()

    @staticmethod
    def _build_fingerprint_diff(old_value, new_value, property_name):
        old_text = (old_value or "").splitlines()
        new_text = (new_value or "").splitlines()
        
        if old_text == new_text:
            return ""
            
        return "\n".join(difflib.unified_diff(
            old_text,
            new_text,
            fromfile=f"{property_name}.old",
            tofile=f"{property_name}.new",
            lineterm="" # Keep this empty, the "\n".join() handles the line breaks
        ))

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

        new_text = utils.clean_text(text)

        if is_modified:
            req.text = new_text
            req.title = title
            req.conformance = conformance
            req.content_hash = fp
        elif req.text != text:
            req.text = new_text

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

        if utils.is_not_equal(req.actor, actor):
            req.actor = actor
            req.date = _now
        if utils.is_not_equal(req.test_procedures, test_procedures):
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

        if req.release_status == 'MODIFIED':

            if self.diff_to_maps:
                diff_map = {}
                for version, version_map in self.diff_to_maps.items():
                    if req.key not in version_map:
                        continue
                    historic_req = version_map[req.key]
                    historic_text = utils.clean_text(historic_req.text) or ""
                    historic_title = historic_req.title or ""
                    historic_conformance = historic_req.conformance or ""

                    diff_map[version] = {
                        "text": FileProcessor._build_fingerprint_diff(historic_text, new_text, "text"),
                        "title": FileProcessor._build_fingerprint_diff(historic_title, title or "", "title"),
                        "conformance": FileProcessor._build_fingerprint_diff(historic_conformance, conformance or "", "conformance"),
                    }

                if diff_map:
                    req.modification_diffs = diff_map
        
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
            updated_rest_of_tag = self.TEST_PROCEDURE_PATTERN.sub(
                self._normalize_test_procedure_tag,
                rest_of_tag
            )
            updated_requirement = updated_start_tag + updated_rest_of_tag
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
            req_key = self._next_key()
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
                if actor_tag.get("name"):
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

    def _normalize_test_procedure_tag(self, match: re.Match) -> str:
        attrs = match.group("attrs") or ""
        id_match = re.search(r'\bid\s*=\s*["\']([^"\']+)["\']', attrs, re.IGNORECASE)
        value = ""
        if id_match:
            tp_key = id_match.group(1)
            try:
                # Local import avoids module import cycles at startup.
                from ..polarion.polarion import load_polarion_mappings
                _, testproc_mapping = load_polarion_mappings()
                mapped = testproc_mapping.get(tp_key)
                if isinstance(mapped, dict):
                    value = mapped.get("name", value)
            except Exception:
                pass
        return f"<testProcedure{attrs}>{value}</testProcedure>"

                
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
