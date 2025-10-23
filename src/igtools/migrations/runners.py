from packaging.version import Version

from .registry import MigrationRegistry
from .errors import MigrationError


def ensure_tool_not_older_than_config(config, tool_version: Version):
    ###
    # Hard stop if the configuration was migrated by a newer igtools than the one running now.
    ###
    if config.migrated_with_version > tool_version:
        raise MigrationError(
            f"The configuration was migrated with igtools {config.migrated_with_version}, "
            f"which is newer than your current installation ({tool_version}).\n"
            "Please upgrade igtools before continuing."
        )



def validate_registry_against_tool_version(registry, tool_version: Version):
    ###
    # Build-time/runtime sanity check: no migration may target a version beyond the tool itself.
    ###
    if not registry.by_from:
        return
    max_to = max(step.to_version for step in registry.by_from.values())
    if max_to > tool_version:
        raise MigrationError(
            f"Invalid migration registry: highest migration target is {max_to}, "
            f"which exceeds the installed igtools version {tool_version}."
        )
    

def latest_registry_version(registry: MigrationRegistry):
    ###
    # Return the highest 'to_version' present in the registry.
    ###
    if not registry.by_from:
        return Version("0.0.0")
    return max(step.to_version for step in registry.by_from.values())


def apply_migrations(config, registry: MigrationRegistry, target: Version, logger=None) -> None:
    ###
    # Execute the chain from the current config version to 'target' (inclusive).
    ###
    chain = registry.path(config.migrated_with_version, target)
    for step in chain:
        if logger:
            logger.info(f"Migrating {step.from_version} -> {step.to_version}: {step.description}")
        step.apply(config=config, logger=logger)

        # Persist only after successful step
        config.migrated_with_version = step.to_version
        config.save()
    if logger:
        logger.info(f"Migration complete. Current schema: {config.migrated_with_version}")
