import os
import sys
import argparse

from .versioning import __APPNAME__, __VERSION__
from .config import ConfigCommand, InitCommand
from .specifications import ReleaseCommand, ProcessCommand, ReleaseNoteCommand, RequirementExportCommand, RequirementImportCommand, DuplicateIDCheckCommand
from .polarion import PolarionExportCommand, PolarionMappingCommand
from .migrations import MigrationCommand

from .utils import cli, logger
from .errors import BaseException

 
def main():
    commands = [
        InitCommand(),
        ConfigCommand(),
        ReleaseCommand(),
        ProcessCommand(),
        DuplicateIDCheckCommand(),
        ReleaseNoteCommand(),
        RequirementExportCommand(),
        RequirementImportCommand(),
        PolarionExportCommand(),
        PolarionMappingCommand(),
        MigrationCommand()
    ]
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-v", "--version", action="version", version=cli.get_version(__APPNAME__, __VERSION__), help="Show program's version number and exit")
    parser.add_argument("-h", "--help", action="store_true", help="Show this help message and exit")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    for cmd in commands:
        cmd.configure_subparser(subparsers)

    args = parser.parse_args()
    cli.print_app_info(app=__APPNAME__, version=__VERSION__)
    try:
        for cmd in commands:
            if cmd.match(args):
                cli.print_command(cmd.title())
                cmd.process(args)
                break
        else:
            parser.print_help()
    except BaseException as e:
        logger.log.error(f"{e}")
        sys.exit(os.EX_DATAERR)
    except KeyboardInterrupt as e:
        logger.log.info("\nBye")
    except Exception as e:
        raise e
    sys.exit(os.EX_OK)



if __name__ == "__main__":
    main()