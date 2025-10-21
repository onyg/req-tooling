from .config import config, CliAppConfig

from ..commands import Command
from ..utils import arguments, cli


class ConfigCommand(Command):

    def configure_subparser(self, subparsers):
        parser = subparsers.add_parser("config", help="Create, update and read a config file")
        parser.add_argument("--edit", action="store_true", help="Create and update the config")
        arguments.add_config(parser=parser)
        return parser

    def match(self, args):
        return getattr(args, "command", None) == "config"

    def run(self, args):
        cli.print_command(f"Config")
        if args.edit:
            CliAppConfig().process()
        else:
            config.set_filepath(filepath=args.config).load()
            CliAppConfig().show()