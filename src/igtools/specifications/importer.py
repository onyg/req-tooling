import os
import json
import yaml
from datetime import datetime

from .manager import ReleaseManager, Processor
from .data import Requirement
from ..errors import ReleaseNotFoundException, FilePathNotExists
from ..utils import cli


class RequirementImporter:
    def __init__(self, config, import_file, release_version=None, next_version=None, dry_run=False):
        self.config = config
        self.import_file = import_file
        self.release = release_version
        self.next = next_version
        self.dry_run = dry_run
        self.release_manager = ReleaseManager(config)

    def import_version(self):
        imported_data = self._load_import_file()
        imported_reqs = [Requirement().deserialize(r) for r in imported_data['requirements']]

        # 1. Create the release for self.release (if not already present)
        try:
            release = self.release_manager.load_version(self.release)
            existing_keys = {req.key for req in release.requirements}
            for req in imported_reqs:
                if req.key not in existing_keys:
                    release.requirements.append(req)
                    existing_keys.add(req.key) 
            if not self.dry_run:
                self.release_manager.save(release)

            cli.print_text(cli.YELLOW, f"Release {self.release} already exists. Skipping creation.")
            
        except ReleaseNotFoundException:
            cli.print_text(cli.GREEN,f"Creating release {self.release} from import file.")

            release = self.release_manager.load()
            release.version = self.release
            release.requirements = imported_reqs
            if not self.dry_run:
                self.release_manager.save(release)
                self.release_manager.archive([r for r in imported_reqs if r.is_deleted])
                self.config.add_release(self.release)
                self.config.save()

        # 2. Compare with next version (if specified)
        if self.next:
            try:
                next_release = self.release_manager.load_version(self.next)
                next_map = {r.key: r for r in next_release.requirements}

                cli.print_text(cli.BLUE, f"Comparing imported version {self.release} with next version {self.next}...")
                cli.print_line()

                changed = []
                for req in imported_reqs:
                    next_req = next_map.get(req.key, None)
                    if req.is_deleted:
                        if next_req and next_req.is_deleted:
                            cli.print_text(cli.RED, f"[-] Removing deleted requirement {req.key} from {self.next}")
                            if not self.dry_run:
                                next_req.for_deletion = True
                                changed.append(req.key)
                        continue

                    if not next_req:
                        cli.print_text(cli.GREEN, f"[+] New in {self.release}, not present in {self.next}: {req.key}")
                        if not self.dry_run:
                            req.is_stable = True
                            next_release.requirements.append(req)
                            changed.append(req.key)
                    else:
                        is_modified = False
                        is_set_to_stable = False
                        if next_req.is_modified and req.is_modified:
                            next_req.is_stable = True
                            is_set_to_stable = True
                        if next_req.is_deleted:
                            continue
                        was_already_modifed = next_req.is_modified
                        next_req = Processor.update_existing_requirement(
                            req=next_req,
                            text=req.text,
                            title=req.title,
                            actor=next_req.actor,
                            file_path=req.source,
                            conformance=req.conformance
                        )
                        if not next_req.is_stable and not was_already_modifed:
                            cli.print_text(cli.YELLOW, f"[~] Updating {req.key} in {self.next} from {self.release}")
                        elif is_set_to_stable:
                            cli.print_text(cli.BLUE, f"[~] Set STABLE {req.key} in {self.next} from {self.release}")

                print("")
                if not self.dry_run:
                    self.release_manager.save(next_release)
                    cli.print_text(cli.YELLOW, f"Updated {len(changed)} requirements in version {self.next}.")
                else:
                    cli.print_text(cli.YELLOW, f"[Dry-run] {len(changed)} updates would be made to version {self.next}.")

            except ReleaseNotFoundException:
                cli.print_text(cli.RED, f"Next version {self.next} not found. Skipping propagation.")

    def _load_import_file(self):
        if not os.path.exists(self.import_file):
            raise FilePathNotExists(f"Import file not found: {self.import_file}")
        with open(self.import_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) if self.import_file.endswith(('.yaml', '.yml')) else json.load(f)

        if isinstance(data, list):
            return {"requirements": data}
        elif "requirements" in data:
            return data
        else:
            raise ValueError("Import file must contain a list of requirements or a dictionary with 'requirements'.")
