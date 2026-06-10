from abc import ABC, abstractmethod
import argparse

from .config import config
from .startup_guard import require_clean_startup


class Command(ABC):
    """
    Abstract base class for CLI commands.
    Each command must define how its subparser is configured,
    how it matches the parsed args, and how it executes (run).
    """

    @property
    def with_startup_guard(self) -> bool:
        return True

    def process(self, args: argparse.Namespace) -> None:
        if getattr(args, "config", None):
            config.set_filepath(filepath=args.config).load()
            if self.with_startup_guard:
                require_clean_startup(config=config)
        return self.run(config=config, args=args)

    @abstractmethod
    def title(self) -> str:
        pass

    @abstractmethod
    def configure_subparser(self, subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
        """
        Configure and return the subparser for this command.
        Example:
            parser = subparsers.add_parser("release", help="Release Management. For example to create a new release version")
            parser.add_argument("--freeze", action="store_true", help="Freeze the current release: compute and store a release hash to lock its state. After freezing, any structural or textual changes will cause integrity check failures.")
            return parser
        """
        pass

    @abstractmethod
    def match(self, args: argparse.Namespace) -> bool:
        """
        Return True if this command should handle the given args.
        Typically compares args.command or similar.
        Example:
            return args.command == "release"
        """
        pass
    
    @abstractmethod
    def run(self, config, args: argparse.Namespace) -> None:
        """
        Execute the command logic.
        Example:
            if args.freeze:
                print("Building in frozen mode...")
        """
        pass
