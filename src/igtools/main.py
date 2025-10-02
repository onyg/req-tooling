import os
import sys
import argparse

from .version import __APPNAME__, __VERSION__
from .config import config, IGConfig, CliAppConfig, CONFIG_DEFAULT_DIR, IG_CONFIG_DEFAULT_FILE
from .specifications import ReleaseManager, Processor, ReleaseNoteManager, RequirementExporter, RequirementImporter
from .polarion import PolarionExporter, DEFAULT_TESTPROCEDURE

from .extractor import FHIRPackageExtractor, FHIR_PACKAGE_DOWNLOAD_FOLDER

from .utils import id, cli
from .errors import BaseException, FrozenReleaseException



def add_common_argument(parser):
    parser.add_argument("--directory", help="Input directory for processing", required=False)
    parser.add_argument("--config", help=f"Directory for configuration files, default is '{CONFIG_DEFAULT_DIR}'", default=CONFIG_DEFAULT_DIR)
    

def main():
    parser = argparse.ArgumentParser(description=cli.get_version(__APPNAME__, __VERSION__))
    parser.add_argument("-v", "--version", action="version", version=cli.get_version(__APPNAME__, __VERSION__))
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Process command
    process_parser = subparsers.add_parser("process", help="Process requirements")
    process_parser.add_argument("--check", action="store_true", help="Check for Duplicate ID")
    # process_parser.add_argument("--output", help="Output directory", required=False)
    add_common_argument(parser=process_parser)


    # Release command
    release_parser = subparsers.add_parser("release", help="Release Management. For example to create a new release version")
    release_parser.add_argument("version", nargs="?", help="New release version")
    release_parser.add_argument("--force", action="store_true", help="Force release with version even if it already exists")
    release_parser.add_argument("--final", action="store_true", help="[DEPRECATED] Marks the release as final and prevents any further changes")
    release_parser.add_argument("--freeze", action="store_true", help="Freeze the current release: compute and store a release hash to lock its state. After freezing, any structural or textual changes will cause integrity check failures.")
    release_parser.add_argument("--unfreeze", action="store_true", help="Unfreeze the current release: remove the frozen state and its release hash. After unfreezing, further modifications to the release are allowed again.")
    release_parser.add_argument("--yes", "-y",action="store_true", help="Automatically confirm all prompts without asking for user input")
    release_parser.add_argument("--is-frozen", action="store_true", help="Checks whether the release has been frozen. If set, no further changes are allowed")
    add_common_argument(parser=release_parser)

    # Create IG Release Notes command
    release_notes_parser = subparsers.add_parser("ig-release-notes", help="Create release notes for a FHIR Implementation Guide")
    release_notes_parser.add_argument("output", help="Output directory")
    release_notes_parser.add_argument("--config", help=f"Directory for configuration files, default is '{CONFIG_DEFAULT_DIR}'", default=CONFIG_DEFAULT_DIR)
    release_notes_parser.add_argument("--filename", help=f"The filename for the release notes export, default is {ReleaseNoteManager.RELEASE_NOTES_FILENAME}", default=ReleaseNoteManager.RELEASE_NOTES_FILENAME)

    # Requirements Exporter command
    exporter_parser = subparsers.add_parser("export", help="Export the requirements")
    exporter_parser.add_argument("output", help="The export output directory")
    exporter_parser.add_argument("--config", help=f"Directory for configuration files, default is '{CONFIG_DEFAULT_DIR}'", default=CONFIG_DEFAULT_DIR)
    exporter_parser.add_argument("--format", help="The export format, default is JSON", default='JSON')
    exporter_parser.add_argument("--filename", help=f"The export filename", required=False)
    exporter_parser.add_argument("--version", "-v", help="Version of the requirements to export, default is 'current'", default="current")
    exporter_parser.add_argument("--with-deleted", action="store_true", help="Export also deleted requirements")

    # Polarion Requirements Exporter command
    polarion_exporter_parser = subparsers.add_parser("polarion", help="Polarion requirements export")
    polarion_exporter_parser.add_argument("output", help="The polarion export output directory")
    polarion_exporter_parser.add_argument("--config", help=f"Directory for configuration files, default is '{CONFIG_DEFAULT_DIR}'", default=CONFIG_DEFAULT_DIR)
    polarion_exporter_parser.add_argument("--filename", help=f"The export filename", required=False)
    polarion_exporter_parser.add_argument("--version", "-v", help="Version of the requirements to export, default is 'current'", default="current")
    polarion_exporter_parser.add_argument("--ig", help="Path to the (FHIR) IG config file (e.g., sushi-config.yaml)", default=IG_CONFIG_DEFAULT_FILE)
    polarion_exporter_parser.add_argument("--default", help="The default test procedure.", default=DEFAULT_TESTPROCEDURE)

    # Requirements Importer command
    importer_parser = subparsers.add_parser("import", help="Import a release version and propagate updates to the next release")
    importer_parser.add_argument("input", help="The requirements file to import (JSON or YAML)")
    importer_parser.add_argument("--release", required=True, help="The release version from which requirements will be imported")
    importer_parser.add_argument("--next", required=False, help="The next version to which changes should be propagated")
    importer_parser.add_argument("--dry-run", action="store_true", help="Simulate the import and propagation without writing changes")
    importer_parser.add_argument("--config", help=f"Directory for configuration files, default is '{CONFIG_DEFAULT_DIR}'", default=CONFIG_DEFAULT_DIR)

    # Config command
    config_parser = subparsers.add_parser("config", help="Create a config file")
    config_parser.add_argument("--show", action="store_true", help="Print the current config")
    config_parser.add_argument("--config", help=f"Directory for configuration files, default is '{CONFIG_DEFAULT_DIR}'", default=CONFIG_DEFAULT_DIR)

    # FHIR Extract command
    fhir_extractor_parser = subparsers.add_parser("fhir-extract", help="Create a config file")
    fhir_extractor_parser.add_argument("--config", help=f"Directory for configuration files, default is '{CONFIG_DEFAULT_DIR}' ", default=CONFIG_DEFAULT_DIR)
    fhir_extractor_parser.add_argument("--extractconfig", help="The configuration files for the FHIR extract", default=None)
    fhir_extractor_parser.add_argument("--download", 
                                       help=f"""
                                            Specifies the folder to download non-installed FHIR packages. 
                                            The FHIR package will be downloaded to this folder to extract its definitions. 
                                            If not provided, the default folder is '{FHIR_PACKAGE_DOWNLOAD_FOLDER}'.
                                            """, 
                                       default=FHIR_PACKAGE_DOWNLOAD_FOLDER)


    # Test command
    test_parser = subparsers.add_parser("test", help="Check for duplicate requirement IDs")
    add_common_argument(parser=test_parser)

    args = parser.parse_args()

    try:
        if args.command == "process":
            cli.print_command_title_with_app_info(app=__APPNAME__, version=__VERSION__, title='Processor')
            config.set_filepath(filepath=args.config).load()
            processor = Processor(config=config, input=args.directory)
            if args.check:
                cli.print_command_title(f"Check {config.current or 'no release version'}")
                processor.check()
            else:
                cli.print_command_title(f"Process release version: {config.current or 'no release version'}")
                processor.process()

        elif args.command == "release":
            config.set_filepath(filepath=args.config).load()
            cli.print_command_title_with_app_info(app=__APPNAME__, version=__VERSION__, title='Release Manager')
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

        elif args.command == "ig-release-notes" and args.output:
            config.set_filepath(filepath=args.config).load()
            cli.print_command_title_with_app_info(app=__APPNAME__, 
                                                  version=__VERSION__, 
                                                  title=f"Create Release-Notes for {config.current} in {os.path.join(args.output, args.filename)}")
            release_note_manager = ReleaseNoteManager(config=config, filename=args.filename)
            release_note_manager.generate(output=args.output)

        elif args.command == "export" and args.output:
            config.set_filepath(filepath=args.config).load()
            filename = args.filename or RequirementExporter.generate_filename(format=args.format, version=args.version)
            cli.print_command_title_with_app_info(app=__APPNAME__, 
                                                  version=__VERSION__, 
                                                  title=f"Export the {config.current} requirements to {os.path.join(args.output, filename)}")
            exporter = RequirementExporter(config=config, format=args.format, filename=args.filename, version=args.version)
            exporter.export(output=args.output, with_deleted=args.with_deleted)

        elif args.command == "polarion" and args.output:
            config.set_filepath(filepath=args.config).load()
            ig_config = IGConfig(config=args.ig).load()
            filename = args.filename or PolarionExporter.generate_filename(version=args.version)
            cli.print_command_title_with_app_info(app=__APPNAME__, 
                                                  version=__VERSION__, 
                                                  title=f"Export the {config.current} requirements for polarion to {os.path.join(args.output, filename)}")
            polarion_exporter = PolarionExporter(config=config, ig_config=ig_config, filename=args.filename, version=args.version, default_test_procedure=args.default)
            polarion_exporter.export(output=args.output)

        elif args.command == "import" and args.input:
            config.set_filepath(filepath=args.config).load()
            cli.print_command_title_with_app_info(
                app=__APPNAME__, version=__VERSION__,
                title=f"Import version {args.release} and propagate to {args.next}"
            )
            importer = RequirementImporter(
                config=config,
                import_file=args.input,
                release_version=args.release,
                next_version=args.next,
                dry_run=args.dry_run
            )
            importer.import_version()

        elif args.command == "config":
            cli.print_command_title_with_app_info(app=__APPNAME__, 
                                                  version=__VERSION__, 
                                                  title=f"Config")
            if args.show:
                config.set_filepath(filepath=args.config).load()
                CliAppConfig().show()
            else:
                try:
                    CliAppConfig().process()
                except KeyboardInterrupt as e:
                    cli.print_command("\nBye")

        elif args.command == 'fhir-extract':
            config.set_filepath(filepath=args.config).load()
            cli.print_command_title_with_app_info(app=__APPNAME__, 
                                                  version=__VERSION__, 
                                                  title=f"Extract FHIR definition, extract config {args.extractconfig}")
            extractor = FHIRPackageExtractor(config=config)
            extractor.process(config_filename=args.extractconfig, download_folder=args.download)


        elif args.command == "test":
            cli.print_command_title_with_app_info(app=__APPNAME__, 
                                                  version=__VERSION__, 
                                                  title="Running test to check for duplicate requirement IDs")
            config.set_filepath(filepath=args.config).load()
            processor = Processor(config=config, input=args.directory)
            processor.check()
            cli.print_command(f"Test completed successfully. No issues detected")
        else:
            parser.print_help()
    except BaseException as e:
        cli.print_error(f"Error: {e}")
        sys.exit(os.EX_DATAERR)
    except KeyboardInterrupt as e:
        cli.print_command("\nBye")
    except Exception as e:
        raise e
    sys.exit(os.EX_OK)



if __name__ == "__main__":
    main()