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
        self.separator = "_"
        self.name = ""
        self.current = None
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
            current=self.current,
            releases=self.releases
        )
    
    def from_dict(self, data):
        self.directory = data.get('directory')
        self.name = data.get('name')
        self.prefix = data.get('prefix')
        self.current = data.get('current', None)
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
        print('Config:')
        print('')

        config_path = input(f"Set config directory (default is {CONFIG_DEFAULT_DIR}): ")
        print(f"Value: {config_path or CONFIG_DEFAULT_DIR}")
        print('')

        directory = None
        while not directory:
            directory = input(f"Set input directory: ")
        print(f"Value: {directory}")
        print('')

        name = None
        while not name:
            name = input(f"Set the name for the projekt: ")
        print(f"Value: {name}")
        print('')

        prefix = input(f"Set the prefix for the requirement id (default is REQ): ")
        print(f"Value: {prefix or 'REQ'}")

        config.set_filepath(config_path or CONFIG_DEFAULT_DIR)
        config.directory = directory
        config.name = name
        config.prefix = prefix or "REQ"

        config.save()

    def show(self):
        headers = [("Current config", {"colspan": 2})]
        rows = []
        rows.append([("Project name", {"colspan": 1}), (config.name or '-', {"colspan": 1})])
        rows.append([("Current release version", {"colspan": 1}), (config.current or '-', {"colspan": 1})])
        rows.append([("ReqId prefix", {"colspan": 1}), (config.prefix or '-', {"colspan": 1})])
        rows.append([("Input directory", {"colspan": 1}), (config.directory or '-', {"colspan": 1})])
        
        print(cli.format_table_with_border(headers=headers, rows=rows, min_width=25))

    def show_current_release(self):
        headers = [("Release Information", {"colspan": 2})]
        rows = []
        rows.append([("Name", {"colspan": 1}), (config.name or '-', {"colspan": 1})])
        rows.append([("Current", {"colspan": 1}), (config.current or '-', {"colspan": 1})])

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
