import os

from ..config import config, CliAppConfig
from ..commands import Command
from ..utils import cli, arguments
from ..errors import FrozenReleaseException

from .release import ReleaseManager
from .processor import Processor
from .releasenotes import ReleaseNoteManager
from .exporter import RequirementExporter
from .importer import RequirementImporter


class ReleaseCommand(Command):

    def configure_subparser(self, subparsers):
        parser = subparsers.add_parser("release", help="Release Management. For example to create a new release version")
        parser.add_argument("version", nargs="?", help="New release version")
        parser.add_argument("--force", action="store_true", help="Force release with version even if it already exists")
        parser.add_argument("--final", action="store_true", help="[DEPRECATED] Marks the release as final and prevents any further changes")
        parser.add_argument("--freeze", action="store_true", help="Freeze the current release: compute and store a release hash to lock its state. After freezing, any structural or textual changes will cause integrity check failures.")
        parser.add_argument("--unfreeze", action="store_true", help="Unfreeze the current release: remove the frozen state and its release hash. After unfreezing, further modifications to the release are allowed again.")
        parser.add_argument("--yes", "-y",action="store_true", help="Automatically confirm all prompts without asking for user input")
        parser.add_argument("--is-frozen", action="store_true", help="Checks whether the release has been frozen. If set, no further changes are allowed")
        arguments.add_common(parser=parser)
        return parser

    def match(self, args):
        return getattr(args, "command", None) == "release"

    def run(self, args):
        cli.print_command('Release Manager')
        config.set_filepath(filepath=args.config).load()
        if args.is_frozen:
            try:
                ReleaseManager(config=config).raise_if_frozen()
                cli.print_text(cli.YELLOW, "Release is not frozen")
            except FrozenReleaseException as e:
                cli.print_text(cli.YELLOW, "Release has been frozen - no further changes allowed")
                sys.exit(1) 
        elif args.final or args.freeze:
            if cli.confirm_action(f"Are you sure you want to freeze the release version {config.current}?", auto_confirm=args.yes):
                release_manager = ReleaseManager(config=config)
                if not release_manager.is_current_release_frozen():
                    processor = Processor(config=config, input=args.directory)
                    processor.process()
                release_manager.freeze_release()
                cli.print_command(f"The release version {config.current} has been successfully frozen. No further changes are allowed.")
        elif args.unfreeze:
            release_manager = ReleaseManager(config=config)
            if release_manager.is_current_release_frozen():
                if cli.confirm_action(f"Are you sure you want to unfreeze the release version {config.frozen_version}?", auto_confirm=args.yes):
                    release_manager.unfreeze_release()
                    cli.print_command(f"Release {config.current} is now unfrozen. Modifications are permitted again.")
            else:
                cli.print_text(cli.YELLOW, f"Release {config.current} is not frozen. Unfreeze skipped.")

        elif args.version:
            if cli.confirm_action(f"Confirm new release version {args.version}?", auto_confirm=args.yes):
                release_manager = ReleaseManager(config=config)

                release_manager.check_new_version(version=args.version, force=args.force)

                processor = Processor(config=config, input=args.directory)
                if not config.current is None:
                    if not release_manager.is_current_release_frozen():
                        processor.process()

                processor.reset_all_meta_tags()

                release_manager.create(version=args.version, force=args.force)
                cli.print_command(f"Release version {args.version} has been successfully created")
        else:
            CliAppConfig().show_current_release()


class ProcessCommand(Command):

    def configure_subparser(self, subparsers):
        parser = subparsers.add_parser("process", help="Process requirements")
        parser.add_argument("--check", action="store_true", help="Check for Duplicate ID")
        arguments.add_common(parser=parser)
        return parser

    def match(self, args):
        return getattr(args, "command", None) == "process"

    def run(self, args):
        cli.print_command('Processor')
        config.set_filepath(filepath=args.config).load()
        processor = Processor(config=config, input=args.directory)
        if args.check:
            cli.print_command_title(f"Check {config.current or 'no release version'}")
            processor.check()
        else:
            cli.print_command_title(f"Process release version: {config.current or 'no release version'}")
            processor.process()


class ReleaseNoteCommand(Command):

    def configure_subparser(self, subparsers):
        parser = subparsers.add_parser("ig-release-notes", help="Create release notes for a FHIR Implementation Guide")
        parser.add_argument("output", help="Output directory")
        parser.add_argument("--filename", help=f"The filename for the release notes export, default is {ReleaseNoteManager.RELEASE_NOTES_FILENAME}", default=ReleaseNoteManager.RELEASE_NOTES_FILENAME)
        arguments.add_config(parser=parser)
        return parser

    def match(self, args):
        return getattr(args, "command", None) == "ig-release-notes" and getattr(args, "output", None)

    def run(self, args):
        cli.print_command(f"Create Release-Notes for {config.current} in {os.path.join(args.output, args.filename)}")
        config.set_filepath(filepath=args.config).load()
        release_note_manager = ReleaseNoteManager(config=config, filename=args.filename)
        release_note_manager.generate(output=args.output)


class RequirementExportCommand(Command):

    def configure_subparser(self, subparsers):
        parser = subparsers.add_parser("export", help="Export the requirements")
        parser.add_argument("output", help="The export output directory")
        parser.add_argument("--format", help="The export format, default is JSON", default='JSON')
        parser.add_argument("--filename", help=f"The export filename", required=False)
        parser.add_argument("--version", "-v", help="Version of the requirements to export, default is 'current'", default="current")
        parser.add_argument("--with-deleted", action="store_true", help="Export also deleted requirements")
        arguments.add_config(parser=parser)
        return parser

    def match(self, args):
        return getattr(args, "command", None) == "export" and getattr(args, "output", None)

    def run(self, args):
        config.set_filepath(filepath=args.config).load()
        filename = args.filename or RequirementExporter.generate_filename(format=args.format, version=args.version)
        cli.print_command(f"Export the {config.current} requirements to {os.path.join(args.output, filename)}")
        exporter = RequirementExporter(config=config, format=args.format, filename=args.filename, version=args.version)
        exporter.export(output=args.output, with_deleted=args.with_deleted)


class RequirementImportCommand(Command):

    def configure_subparser(self, subparsers):
        parser = subparsers.add_parser("import", help="Import a release version and propagate updates to the next release")
        parser.add_argument("input", help="The requirements file to import (JSON or YAML)")
        parser.add_argument("--release", required=True, help="The release version from which requirements will be imported")
        parser.add_argument("--next", required=False, help="The next version to which changes should be propagated")
        parser.add_argument("--dry-run", action="store_true", help="Simulate the import and propagation without writing changes")
        arguments.add_config(parser=parser)
        return parser

    def match(self, args):
        return getattr(args, "command", None) == "import" and getattr(args, "input", None)

    def run(self, args):
        config.set_filepath(filepath=args.config).load()
        cli.print_command(f"Import version {args.release} and propagate to {args.next}")
        importer = RequirementImporter(
            config=config,
            import_file=args.input,
            release_version=args.release,
            next_version=args.next,
            dry_run=args.dry_run
        )
        importer.import_version()


class DuplicateIDCheckCommand(Command):

    def configure_subparser(self, subparsers):
        parser = subparsers.add_parser("test", help="Check for duplicate requirement IDs")
        arguments.add_common(parser=parser)
        return parser

    def match(self, args):
        return getattr(args, "command", None) == "test"

    def run(self, args):
        config.set_filepath(filepath=args.config).load()
        cli.print_command("Running test to check for duplicate requirement IDs")
        processor = Processor(config=config, input=args.directory)
        processor.check()
        cli.print_command(f"Test completed successfully. No issues detected")

    