from packaging.version import Version
from typing import Iterable

from .base import Migration
from .errors import MigrationRuntimeError
from .steps import (
    DropActorsAndTestProceduresFromContentHash
)



class MigrationRegistry:
    """
    A registry that holds all known migrations and ensures correct sequencing.
    It maps 'from_version' -> Migration, enforcing a strict linear path between versions.
    """

    @classmethod
    def build(cls):
        return cls([
            DropActorsAndTestProceduresFromContentHash(),
        ])

    def __init__(self, steps: Iterable[Migration]):
        self.by_from = {m.from_version: m for m in steps}

    def path(self, current: Version, target: Version):
        """
        Resolve the ordered list of migrations required to move from
        'current' to 'target' version.

        Raises:
            RuntimeError if no valid migration path exists, or if a cycle is detected.
        """
        chain = []
        v = current
        visited = set()

        while v != target:
            if v in visited:
                raise MigrationRuntimeError("Cycle detected in migration graph.")
            visited.add(v)

            step = self.by_from.get(v)
            if not step:
                raise MigrationRuntimeError(f"No migration step found from {v} towards {target}.")
            chain.append(step)
            v = step.to_version

        return chain
