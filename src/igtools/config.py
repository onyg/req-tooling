# -*- coding: utf-8 -*-
import os
import yaml

from .utils import cli
from .errors import ConfigPathNotExists


CONFIG_DEFAULT_DIR = '.igtools'

CONFIG_FILE = 'config.yaml'

class Config(object):

    def __init__(self, defaults=None, **kwargs):
        super(Config, self).__init__()
        self.path = CONFIG_DEFAULT_DIR
        self.directory = None
        self.prefix = "REQ"
        self.suffix = None
        self.separator = "_"
        self.name = ""
        self.current = None
        self.final = None
        self.releases = []

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
            suffix=self.suffix,
            current=self.current,
            final=self.final,
            releases=self.releases
        )
    
    def from_dict(self, data):
        self.directory = data.get('directory')
        self.name = data.get('name')
        self.prefix = data.get('prefix')
        self.suffix = data.get('suffix', None)
        self.current = data.get('current', None)
        self.final = data.get('final', None)
        self.releases = data.get('releases', [])

    def save(self):
        config_filepath = os.path.join(self.path, CONFIG_FILE)
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        with open(config_filepath, 'w', encoding='utf-8') as file:
            yaml.dump(self.to_dict(), file, default_flow_style=False, allow_unicode=True)

    def load(self):
        config_filepath = os.path.join(self.path, CONFIG_FILE)
        if not os.path.exists(config_filepath):
            raise ConfigPathNotExists(f"The config filepath {config_filepath} does not exists")
        with open(config_filepath, 'r', encoding='utf-8') as file:
            _data = yaml.safe_load(file)
            self.from_dict(data=_data)


config = Config()


class CliAppConfig(object):

    def __init__(self):
        pass

    def process(self):

        def get_default_input_text(value=None):
            return f"{f' (default is {value})' if value else ''}"
        
        print('Config:')
        print('')
        config_path = input(f"Set config directory (default is {CONFIG_DEFAULT_DIR}): ")
        print(f"Config directory: {config_path or CONFIG_DEFAULT_DIR}")
        print('')

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

        suffix = input(f"Set the suffix for the requirement id (default is {config.suffix if config.suffix else 'empty'}): ") or config.suffix
        if suffix:
            suffix = str(suffix).upper()
        print(f"Value for the suffix: {suffix or 'empty'}")

        config.set_filepath(config_path or CONFIG_DEFAULT_DIR)
        config.directory = directory
        config.name = name
        config.prefix = prefix
        config.suffix = suffix

        config.save()
        print('Saved to config')

    def show(self):
        headers = [("Current config", {"colspan": 2})]
        rows = []
        rows.append([("Project name", {"colspan": 1}), (config.name or '-', {"colspan": 1})])
        rows.append([("Current release version", {"colspan": 1}), (config.current or '-', {"colspan": 1})])
        rows.append([("Last final release version", {"colspan": 1}), (config.final or '-', {"colspan": 1})])
        rows.append([("ReqId prefix", {"colspan": 1}), (config.prefix or '-', {"colspan": 1})])
        rows.append([("ReqId suffix", {"colspan": 1}), (config.suffix or '-', {"colspan": 1})])
        rows.append([("Input directory", {"colspan": 1}), (config.directory or '-', {"colspan": 1})])
        
        print(cli.format_table_with_border(headers=headers, rows=rows, min_width=25))

    def show_current_release(self):
        headers = [("Release Information", {"colspan": 2})]
        rows = []
        rows.append([("Name", {"colspan": 1}), (config.name or '-', {"colspan": 1})])
        rows.append([("Current", {"colspan": 1}), (config.current or '-', {"colspan": 1})])
        rows.append([("Last final ", {"colspan": 1}), (config.final or '-', {"colspan": 1})])

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
