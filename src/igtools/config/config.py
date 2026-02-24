# -*- coding: utf-8 -*-
import os
import yaml

from packaging.version import Version, InvalidVersion

from ..versioning import __VERSION__
from ..utils import cli, logger
from ..errors import ConfigPathNotExists, InitConfigExistsError


CONFIG_DEFAULT_DIR = '.igtools'

CONFIG_FILE = 'config.yaml'

IG_CONFIG_DEFAULT_FILE = 'sushi-config.yaml' 



class BaseConfig(object):

    def __init__(self, config):
        self.config_file = config


    def load(self):
        if not os.path.exists(self.config_file):
            raise ConfigPathNotExists(f"The config filepath {self.config_file} does not exists")
        with open(self.config_file, 'r', encoding='utf-8') as file:
            _data = yaml.safe_load(file)
            self.from_dict(data=_data)
        return self

    def from_dict(self, data):
        pass


class IGConfig(BaseConfig):

    def __init__(self, config=None):
        self.config_file = config or os.path.join(".", IG_CONFIG_DEFAULT_FILE)
        self.name = None
        self.version = None
        self.canonical = None
        self.title = None
        self.date = None

    def from_dict(self, data):
        self.name = data.get('name', None)
        self.version = data.get('version', None)
        self.canonical = data.get('canonical', None)
        self.title = data.get('title', None)
        self.date = data.get('date', None)

    @property
    def link(self):
        if self.canonical and self.version:
            return f"{self.canonical}/{self.version}"
        return ""


class Config(BaseConfig):

    def __init__(self, defaults=None, **kwargs):
        self.path = CONFIG_DEFAULT_DIR
        self.directory = None
        self.prefix = "REQ"
        self.scope = None
        self.separator = "-"
        self.name = ""
        self.current = None
        self.frozen_version = None
        self.releases = []
        self.frozen_hash = None
        self._migrated_with_version = None
        self.key_mode = "random"  # "random" or "sequential"
        self.current_req_number = 0

    @property
    def config_file(self):
        return os.path.join(self.path, CONFIG_FILE)

    @property
    def migrated_with_version(self):
        _version = None
        try:
            if self._migrated_with_version is None:
                _version = Version("0.0.0")
            elif isinstance(self._migrated_with_version, Version):
                _version = self._migrated_with_version
            else:
                _version = Version(self._migrated_with_version)
        except TypeError:
            return Version("0.0.0")
        except InvalidVersion:
            return Version("0.0.0")
        return _version

    @migrated_with_version.setter
    def migrated_with_version(self, value):
        self._migrated_with_version = str(value)

    def set_filepath(self, filepath):
        self.path = filepath or CONFIG_DEFAULT_DIR
        return self
    
    def add_release(self, version):
        if version not in self.releases:
            self.releases.append(version)

    def to_dict(self):
        return dict(
            directory=self.directory,
            name=self.name,
            prefix=self.prefix,
            scope=self.scope,
            current=self.current,
            frozen_version=self.frozen_version,
            releases=sorted(self.releases),
            frozen_hash=self.frozen_hash,
            migrated_with_version=self._migrated_with_version,
            key_mode=self.key_mode,
            current_req_number=self.current_req_number
        )
    
    def from_dict(self, data):
        self.directory = data.get('directory')
        self.name = data.get('name')
        self.prefix = data.get('prefix')
        self.scope = data.get('scope', None)
        self.current = data.get('current', None)
        self.frozen_version = data.get('final', None)
        self.frozen_version = data.get('frozen_version', None)
        self.releases = sorted(data.get('releases', []))
        self.frozen_hash = data.get('frozen_hash', None)
        self._migrated_with_version = data.get('migrated_with_version', None)
        self.key_mode = data.get('key_mode', 'random') or 'random'
        self.current_req_number = data.get('current_req_number', 0) or 0

    def save(self):
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        with open(self.config_file, 'w', encoding='utf-8') as file:
            yaml.dump(self.to_dict(), file, default_flow_style=False, allow_unicode=True)


config = Config()


class CliAppConfig(object):

    def __init__(self, is_initialize=False):
        self.is_initialize = is_initialize

    def process(self):

        def get_default_input_text(value=None):
            return f"{f' (default is {value})' if value else ''}"
        
        print('')
        config_path = input(f"Set config directory (default is {CONFIG_DEFAULT_DIR}): ")
        print(f"Config directory: {config_path or CONFIG_DEFAULT_DIR}")
        print('')

        if self.is_initialize:
            config_file_path = os.path.join(config_path or CONFIG_DEFAULT_DIR, CONFIG_FILE)
            if os.path.exists(config_file_path):
                raise InitConfigExistsError(f"Initialization aborted: A configuration file already exists at '{config_file_path}'")

        try:
            config.set_filepath(filepath=config_path).load()
        except ConfigPathNotExists as e:
            pass

        directory = None
        while not directory:
            directory = input(f"Set input directory{get_default_input_text(value=config.directory)}: ") or config.directory
        print(f"Value for the directory: {directory}")
        print('')

        name = None
        while not name:
            name = input(f"Set the name for the projekt{get_default_input_text(value=config.name)}: ") or config.name
        print(f"Value for the name: {name}")
        print('')

        prefix = None
        while not prefix:
            prefix = input(f"Set the prefix for the requirement id{get_default_input_text(value=config.prefix)}: ") or config.prefix
            if prefix:
                prefix = str(prefix).upper()
        print(f"Value for the prefix: {prefix}")
        print('')

        scope = input(f"Set the scope for the requirement id (default is {config.scope if config.scope else 'empty'}): ") or config.scope
        if scope:
            scope = str(scope).upper()
        print(f"Value for the scope: {scope or 'empty'}")
        print('')

        key_mode = input(f"Set key mode (random/sequential){get_default_input_text(value=config.key_mode)}: ") or config.key_mode
        if key_mode not in ['random', 'sequential']:
            print(f"Invalid mode '{key_mode}', using 'random'")
            key_mode = 'random'
        print(f"Value for key mode: {key_mode}")

        config.set_filepath(config_path or CONFIG_DEFAULT_DIR)
        config.directory = directory
        config.name = name
        config.prefix = prefix
        config.scope = scope
        config.key_mode = key_mode

        config.save()
        print('Saved to config')
        return config

    def show(self):
        headers = [("Current config", {"colspan": 2})]
        rows = []
        rows.append([(f"App version", {"colspan": 1}), (f"{__VERSION__}", {"colspan": 1})])
        rows.append([("Migrated with app version", {"colspan": 1}), (config.migrated_with_version or '-', {"colspan": 1})])
        rows.append("separator")
        rows.append([("Project name", {"colspan": 1}), (config.name or '-', {"colspan": 1})])
        rows.append([("ReqId prefix", {"colspan": 1}), (config.prefix or '-', {"colspan": 1})])
        rows.append([("ReqId scope", {"colspan": 1}), (config.scope or '-', {"colspan": 1})])
        rows.append([("ReqId key mode", {"colspan": 1}), (config.key_mode or 'random', {"colspan": 1})])
        if config.key_mode == "sequential":
            rows.append([("Current key number", {"colspan": 1}), (config.current_req_number, {"colspan": 1})])
        rows.append([("Input directory", {"colspan": 1}), (config.directory or '-', {"colspan": 1})])
        rows.append("separator")
        rows.append([("Current release version", {"colspan": 1}), (config.current or '-', {"colspan": 1})])
        rows.append([("Last frozen release version", {"colspan": 1}), (config.frozen_version or '-', {"colspan": 1})])
        
        print(cli.format_table_with_border(headers=headers, rows=rows, min_width=25))

    def show_current_release(self):
        headers = [("Release Information", {"colspan": 2})]
        rows = []
        rows.append([("Name", {"colspan": 1}), (config.name or '-', {"colspan": 1})])
        rows.append([("Current", {"colspan": 1}), (config.current or '-', {"colspan": 1})])
        rows.append([("Last frozen ", {"colspan": 1}), (config.frozen_version or '-', {"colspan": 1})])

        if config.releases:
            rows.append("separator")
            count = 0
            for r in config.releases:
                if count == 0:
                    label = "Releases"
                else:
                    label = ""
                rows.append([(label, {}), (r, {})])
                count += 1

        print(cli.format_table_with_border(headers=headers, rows=rows, min_width=25))
