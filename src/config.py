# -*- coding: utf-8 -*-
import os
import json


CONFIG_DEFAULT_DIR = '.igtools'


class Config(object):

    def __init__(self, defaults=None, **kwargs):
        super(Config, self).__init__()
        self.path = CONFIG_DEFAULT_DIR
        self.directory = None
        self.prefix = "REQ"
        self.name = ""
        self.max_id = 0
        self.current = None

    def set_filepath(self, filepath):
        self.path = filepath or CONFIG_DEFAULT_DIR
        return self

    def to_dict(self):
        return dict(
            directory=self.directory,
            name=self.name,
            prefix=self.prefix,
            maxID=self.max_id,
            current=self.current
        )
    
    def from_dict(self, data):
        self.directory = data.get('directory')
        self.name = data.get('name')
        self.prefix = data.get('prefix')
        self.max_id = data.get('maxID')
        self.current = data.get('current', None)

    def save(self):
        config_filepath = os.path.join(self.path, "config.json")
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        with open(config_filepath, 'w', encoding='utf-8') as file:
            json.dump(self.to_dict(), file, indent=4, ensure_ascii=False)

    def load(self):
        config_filepath = os.path.join(self.path, "config.json")
        if not os.path.exists(config_filepath):
            raise Exception('TODO: Custom Exception for the usecase')
        with open(config_filepath, 'r', encoding='utf-8') as file:
            _data = json.load(file)
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
        print('Current config:')
        print('')
        print(f"Project name: {config.name}")
        print(f"Current release version: {config.current}")
        print(f"ReqId prefix: {config.prefix}")
        print(f"Max reqId: {config.prefix}-{config.max_id:05d}")
        print(f"Input directory: {config.directory}")

