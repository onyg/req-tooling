import argparse

from .config import CliAppConfig

from ..commands import Command
from ..utils import arguments, cli

from ..migrations.registry import MigrationRegistry
from ..migrations.runners import latest_registry_version


class ConfigCommand(Command):

    def title(self) -> str:
        return "Config"

    def configure_subparser(self, subparsers):
        parser = subparsers.add_parser("config", help="Read or edit the igtools configuration")
        parser.add_argument("--edit", action="store_true", help="Edit the igtools configuration")
        arguments.add_config(parser=parser)
        return parser

    def match(self, args):
        return getattr(args, "command", None) == "config"

    def run(self, config, args):
        if args.edit:
            CliAppConfig().process()
        else:
            CliAppConfig().show()



class InitCommand(Command):

    def title(self) -> str:
        return "Init project"

    def process(self, args: argparse.Namespace) -> None:
        return self.run(config=None, args=args)

    def configure_subparser(self, subparsers):
        parser = subparsers.add_parser("init", help="Initialize a new igtools configuration in the current working directory")
        return parser

    def match(self, args):
        return getattr(args, "command", None) == "init"

    def run(self, config, args):
        config_app = CliAppConfig(is_initialize=True)
        config = config_app.process()
        config.migrated_with_version = latest_registry_version(registry=MigrationRegistry.build())
        config.save()