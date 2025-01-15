import os
import json
import time
import sys
import argparse

from .config import config, CliAppConfig, CONFIG_DEFAULT_DIR
from .specifications import ReleaseManager, Processor, ReleaseNoteManager

from .utils import id
from .errors import BaseException

__VERSION__ = '0.0.1'


def confirm_action(prompt, auto_confirm=False):
    """
    :param prompt: The confirmation message to display.
    :param auto_confirm: If True, skips confirmation and returns True.
    :return: True if confirmed, False otherwise.
    """
    if auto_confirm:
        return True

    while True:
        choice = input(f"{prompt} [y/N]: ").strip().lower()
        if choice in ["y", "yes"]:
            return True
        elif choice in ["n", "no", ""]:
            return False
        else:
            print("Please respond with 'y' or 'n'.")


def add_common_argument(parser):
    parser.add_argument("--directory", help="Input directory for processing", required=False)
    parser.add_argument("--config", help="Directory for configuration files", default=CONFIG_DEFAULT_DIR)
    

def main():
    parser = argparse.ArgumentParser(description="Requirement Management Tool")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Process command
    process_parser = subparsers.add_parser("process", help="Process requirements")
    process_parser.add_argument("--check", action="store_true", help="Check for Duplicate ID")
    add_common_argument(parser=process_parser)


    # Release command
    release_parser = subparsers.add_parser("release", help="Release Management. For example to create a new release version")
    release_parser.add_argument("version", nargs="?", help="New release version")
    release_parser.add_argument("--force", action="store_true", help="Force release with version even if it already exists")
    release_parser.add_argument("--final", action="store_true", help="Marks the release as final and prevents any further changes")
    release_parser.add_argument("--yes", action="store_true", help="Automatically confirm all prompts without asking for user input")
    add_common_argument(parser=release_parser)

    # Create Release Notes command
    release_notes_parser = subparsers.add_parser("release-notes", help="Create a release notes")
    release_notes_parser.add_argument("--output", help="Output directory")
    release_notes_parser.add_argument("--config", help="Directory for configuration files", default=CONFIG_DEFAULT_DIR)

    # Config command
    config_parser = subparsers.add_parser("config", help="Create a config file")
    config_parser.add_argument("--show", action="store_true", help="Print the current config")
    config_parser.add_argument("--config", help="Directory for configuration files", default=CONFIG_DEFAULT_DIR)

    # Test command
    test_parser = subparsers.add_parser("test", help="Test")
    add_common_argument(parser=test_parser)

    args = parser.parse_args()

    try:
        print(f"IGTOOLS (v{__VERSION__})")
        if args.command == "process":
            config.set_filepath(filepath=args.config).load()
            processor = Processor(config=config, input=args.directory)
            if args.check:
                print(f"Check {config.current or 'no release version'}")
                processor.check()
            else:
                print(f"Process {config.current or 'no release version'}")
                processor.process()

        elif args.command == "release":
            config.set_filepath(filepath=args.config).load()
            print(f"Release Manager")
            if args.final:
                if confirm_action(f"Are you sure you want to finalize the release version {config.current}?", auto_confirm=args.yes):
                    ReleaseManager(config=config).set_current_as_final()
                    print(f"The release version {config.current} has been successfully finalized. No further changes are allowed")
            elif args.version:
                if confirm_action(f"Confirm new release version {args.version}?", auto_confirm=args.yes):
                    release_manager = ReleaseManager(config=config)

                    release_manager.check_new_version(version=args.version, force=args.force)

                    if not config.current is None:
                        if not release_manager.is_current_final():
                            processor = Processor(config=config, input=args.directory)
                            processor.process()

                    release_manager.create(version=args.version, force=args.force)
                    print(f"Release version {args.version} has been successfully created")
            else:
                CliAppConfig().show_current_release()

        elif args.command == "release-notes" and args.output:
            config.set_filepath(filepath=args.config).load()
            print(f"Create Release-Notes for {config.current} in {args.output}")
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
            print(f"Running test to check for duplicate requirement IDs")
            config.set_filepath(filepath=args.config).load()
            processor = Processor(config=config, input=args.directory)
            processor.check()
            print(f"Test completed successfully. No issues detected")
        else:
            parser.print_help()

    except BaseException as e:
        print(f"Error: {e}")
        sys.exit(os.EX_DATAERR)
    except KeyboardInterrupt as e:
        print("\nBye")
    except Exception as e:
        raise e
    sys.exit(os.EX_OK)



if __name__ == "__main__":
    main()