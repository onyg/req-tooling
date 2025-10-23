from ..commands import Command
from ..utils import cli, arguments, logger
from ..versioning import __VERSION__

from .errors import MigrationError
from .registry import MigrationRegistry
from .runners import apply_migrations, latest_registry_version, ensure_tool_not_older_than_config, validate_registry_against_tool_version




class MigrationCommand(Command):

    def title(self) -> str:
        return "Migration"

    @property
    def with_startup_guard(self) -> bool:
        return False

    def configure_subparser(self, subparsers):
        parser = subparsers.add_parser("migrate", help="Run all pending igtools migrations")
        parser.add_argument("--dry-run", action="store_true", help="Show planned steps without applying")
        arguments.add_config(parser=parser)
        return parser

    def match(self, args):
        return getattr(args, "command", None) == "migrate"

    def run(self, config, args):
        ensure_tool_not_older_than_config(config=config, tool_version=__VERSION__)

        registry = MigrationRegistry.build()
        target = latest_registry_version(registry=registry)
        validate_registry_against_tool_version(registry=registry, tool_version=__VERSION__)

        if config.migrated_with_version >= target:
            logger.log.info("Nothing to migrate. Already up to date.")
            return

        if args.dry_run:
            chain = registry.path(config.migrated_with_version, target)
            logger.log.info("Planned migrations:")
            for s in chain:
                logger.log.info(f"{s.from_version} -> {s.to_version}: {s.description}")
            logger.log.info(f"Final target: {target}")
            return

        apply_migrations(config, registry, target=target, logger=logger.log)
        logger.log.info("-"*10)
        logger.log.info(f"Migration finished. Current schema: {config.migrated_with_version}")