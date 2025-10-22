from .config import CliAppConfig

from ..commands import Command
from ..utils import arguments, cli


class ConfigCommand(Command):

    def title(self) -> str:
        return "Config"

    def configure_subparser(self, subparsers):
        parser = subparsers.add_parser("config", help="Create, update and read a config file")
        parser.add_argument("--edit", action="store_true", help="Create and update the config")
        arguments.add_config(parser=parser)
        return parser

    def match(self, args):
        return getattr(args, "command", None) == "config"

    def run(self, config, args):
        if args.edit:
            CliAppConfig().process()
        else:
            CliAppConfig().show()