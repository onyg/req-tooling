from ..config import config, IGConfig, CliAppConfig, IG_CONFIG_DEFAULT_FILE
from ..commands import Command
from ..utils import cli, arguments

from .polarion import PolarionExporter, PolarionCliView


class PolarionExportCommand(Command):
    def configure_subparser(self, subparsers):
        parser = subparsers.add_parser("polarion", help="Polarion requirements export")
        parser.add_argument("output", help="The polarion export output directory or export file")
        parser.add_argument("--version", "-v", help="Version of the requirements to export, default is 'current'", default="current")
        parser.add_argument("--ig", help="Path to the (FHIR) IG config file (e.g., sushi-config.yaml)", default=IG_CONFIG_DEFAULT_FILE)
        arguments.add_config(parser=parser)
        return parser

    def match(self, args):
        return getattr(args, "command", None) == "polarion" and getattr(args, "output", None)

    def run(self, args):
        config.set_filepath(filepath=args.config).load()
        filepath = PolarionExporter.generate_filepath(output=args.output, version=args.version)
        cli.print_command(f"Export the {config.current} requirements for polarion to {filepath}")

        ig_config = IGConfig(config=args.ig).load()
        polarion_exporter = PolarionExporter(config=config, ig_config=ig_config, version=args.version)
        polarion_exporter.export(output=args.output)


class PolarionMappingCommand(Command):
    def configure_subparser(self, subparsers):
        parser = subparsers.add_parser("polarion-mapping", help="The current polarion mapping (Product Type and Test Procedure")
        return parser

    def match(self, args):
        return getattr(args, "command", None) == "polarion-mapping"

    def run(self, args):
        PolarionCliView.product_type_mapping()
        PolarionCliView.test_proc_mapping()
        PolarionCliView.test_proc_default_mapping()
