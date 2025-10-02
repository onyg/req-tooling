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
        return self.is_current_final()
