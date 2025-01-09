import os
import json
import argparse

from .config import config, CliAppConfig, CONFIG_DEFAULT_DIR
from .specifications import ReleaseManager, Processor, ReleaseNoteManager


def main():
    parser = argparse.ArgumentParser(description="Requirement Management Tool")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # parser.add_argument("--config", help="Directory for configuration files", default=CONFIG_DEFAULT_DIR)

    # Process command
    process_parser = subparsers.add_parser("process", help="Process requirements")
    process_parser.add_argument("--directory", help="Input directory for processing", required=False)
    process_parser.add_argument("--config", help="Directory for configuration files", default=CONFIG_DEFAULT_DIR)
    process_parser.add_argument("--reset", action="store_true", help="Reset the configuration max id")

    # Release command
    release_parser = subparsers.add_parser("release", help="Create a new release version")
    release_parser.add_argument("--newversion", help="New release version")
    release_parser.add_argument("--config", help="Directory for configuration files", default=CONFIG_DEFAULT_DIR)

    # Create Release Notes command
    release_notes_parser = subparsers.add_parser("release-notes", help="Create a release notes")
    release_notes_parser.add_argument("--output", help="Output directory")
    release_notes_parser.add_argument("--config", help="Directory for configuration files", default=CONFIG_DEFAULT_DIR)

    # Config command
    config_parser = subparsers.add_parser("config", help="Create a config file")
    config_parser.add_argument("--show", action="store_true", help="Print the current config")
    config_parser.add_argument("--config", help="Directory for configuration files", default=CONFIG_DEFAULT_DIR)

    args = parser.parse_args()

    if args.command == "process":
        config.set_filepath(filepath=args.config).load()
        _processor = Processor(config=config, input=args.directory)
        _processor.process(reset=args.reset)

    elif args.command == "release" and args.newversion:
        config.set_filepath(filepath=args.config).load()
        _release = ReleaseManager(config=config)
        _release.create(version=args.newversion)
    elif args.command == "release":
        config.set_filepath(filepath=args.config).load()
        CliAppConfig().show_current_release()

    elif args.command == "release-notes" and args.output:
        config.set_filepath(filepath=args.config).load()
        _release_notes = ReleaseNoteManager(config=config)
        _release_notes.generate(output=args.output)

    elif args.command == "config":
        if args.show:
            config.set_filepath(filepath=args.config).load()
            CliAppConfig().show()
        else:
            try:
                CliAppConfig().process()
            except KeyboardInterrupt as e:
                print("\nBye")
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()