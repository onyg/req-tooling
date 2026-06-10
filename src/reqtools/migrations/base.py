from abc import ABC, abstractmethod
from packaging.version import Version


class Migration(ABC):
    """
    Abstract base class representing a single migration step.
    Each migration moves the system from one schema version to the next.
    """

    # Define start and end versions explicitly in subclasses
    from_version: Version
    to_version: Version
    description: str = ""

    def __init__(self):
        # Validate that subclasses have defined the required attributes
        if not hasattr(self, "from_version") or not hasattr(self, "to_version"):
            raise TypeError("Migration must define 'from_version' and 'to_version'.")

    @abstractmethod
    def apply(self, config, context) -> None:
        """
        Execute the migration logic.

        Args:
            config: The IG configuration object. It contains metadata such as
                    the last successfully migrated version and persistent settings.

        Raises: Any exception to signal a failed migration step. Failures stop the chain.
        """
        pass

