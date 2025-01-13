import os
import json
import time
import sys
import argparse

from .config import config, CliAppConfig, CONFIG_DEFAULT_DIR
from .specifications import ReleaseManager, Processor, ReleaseNoteManager

from .utils import id
from .errors import BaseException


def main():
    parser = argparse.ArgumentParser(description="Requirement Management Tool")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Process command
    process_parser = subparsers.add_parser("process", help="Process requirements")
    process_parser.add_argument("--directory", help="Input directory for processing", required=False)
    process_parser.add_argument("--config", help="Directory for configuration files", default=CONFIG_DEFAULT_DIR)
    process_parser.add_argument("--check", action="store_true", help="Check for Duplicate ID")


    # Release command
    release_parser = subparsers.add_parser("release", help="Create a new release version")
    # release_parser.add_argument("--newversion", help="New release version")
    release_parser.add_argument("version", nargs="?", help="New release version")
    release_parser.add_argument("--directory", help="Input directory for pre release processing", required=False)
    release_parser.add_argument("--config", help="Directory for configuration files", default=CONFIG_DEFAULT_DIR)
    release_parser.add_argument("--force", action="store_true", help="Force release with version even if it already exists")
    # release_parser.add_argument("--final", action="store_true", help="Marks the release as final and prevents any further changes")

    # Create Release Notes command
    release_notes_parser = subparsers.add_parser("release-notes", help="Create a release notes")
    release_notes_parser.add_argument("--output", help="Output directory")
    release_notes_parser.add_argument("--config", help="Directory for configuration files", default=CONFIG_DEFAULT_DIR)

    # Config command
    config_parser = subparsers.add_parser("config", help="Create a config file")
    config_parser.add_argument("--show", action="store_true", help="Print the current config")
    config_parser.add_argument("--config", help="Directory for configuration files", default=CONFIG_DEFAULT_DIR)

    test_parser = subparsers.add_parser("test", help="Test")

    args = parser.parse_args()

    try:

        if args.command == "process":
            config.set_filepath(filepath=args.config).load()
            processor = Processor(config=config, input=args.directory)
            if args.check:
                processor.check()
            else:
                processor.process()

        elif args.command == "release":
            config.set_filepath(filepath=args.config).load()

            if args.version:
                release_manager = ReleaseManager(config=config)

                release_manager.check_new_version(version=args.version, force=args.force)

                if not config.current is None:
                    processor = Processor(config=config, input=args.directory)
                    processor.process()

                release_manager.create(version=args.version, force=args.force)
            else:
                CliAppConfig().show_current_release()

        elif args.command == "release-notes" and args.output:
            config.set_filepath(filepath=args.config).load()
            release_note_manager = ReleaseNoteManager(config=config)
            release_note_manager.generate(output=args.output)

        elif args.command == "config":
            if args.show:
                config.set_filepath(filepath=args.config).load()
                CliAppConfig().show()
            else:
                try:
                    CliAppConfig().process()
                except KeyboardInterrupt as e:
                    print("\nBye")

        elif args.command == "test":
            for _ in range(100000):
                print(f"{id.generate_id(prefix='MHD')} - Anzahl {len(id.generated_ids)}")
        else:
            parser.print_help()

    except BaseException as e:
        print(f"Error: {e}")
        sys.exit(os.EX_DATAERR)
    except Exception as e:
        raise e
    sys.exit(os.EX_OK)



if __name__ == "__main__":
    main()