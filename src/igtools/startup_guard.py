from .versioning import __VERSION__
from .errors import StartUpError



def require_clean_startup(config):
    require_clean_migration_state(config)


def require_clean_migration_state(config):

    from .migrations.registry import MigrationRegistry
    from .migrations.runners import latest_registry_version, ensure_tool_not_older_than_config, validate_registry_against_tool_version

    ensure_tool_not_older_than_config(config=config, tool_version=__VERSION__)
    migration_registry = MigrationRegistry.build()
    validate_registry_against_tool_version(registry=migration_registry, tool_version=__VERSION__)

    migration_target = latest_registry_version(registry=migration_registry, tool_version=__VERSION__)

    if config.migrated_with_version < migration_target:
        raise StartUpError(
            f"Startup blocked: pending migrations detected.\n"
            f"The current configuration was last migrated with igtools {config.migrated_with_version}, "
            f"but this installation includes newer schema changes up to {migration_target}.\n\n"
            "Please run 'igtools migrate' to apply the required migration steps before using this version."
        )