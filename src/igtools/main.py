import os
import sys
import argparse

from .version import __APPNAME__, __VERSION__
from .config import ConfigCommand
from .specifications import ReleaseCommand, ProcessCommand, ReleaseNoteCommand, RequirementExportCommand, RequirementImportCommand, DuplicateIDCheckCommand
from .polarion import PolarionExportCommand, PolarionMappingCommand

from .utils import cli
from .errors import BaseException

 
def main():
    commands = [
        ReleaseCommand(),
        ProcessCommand(),
        ReleaseNoteCommand(),
        RequirementExportCommand(),
        PolarionExportCommand(),
        PolarionMappingCommand(),
        RequirementImportCommand(),
        ConfigCommand(),
        DuplicateIDCheckCommand()
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
                cmd.run(args)
                break
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