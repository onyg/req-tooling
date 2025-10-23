import os
import json
import pytest

from typing import Iterable
from unittest.mock import patch, mock_open, MagicMock
from packaging.version import Version

from igtools.migrations.errors import MigrationError, MigrationRuntimeError
from igtools.migrations.base import Migration
from igtools.migrations.registry import MigrationRegistry
from igtools.migrations.runners import apply_migrations


class StubConfig:
    def __init__(self, v: str):
        self.migrated_with_version = Version(v)
        self._saves = 0

    def save(self):
        self._saves += 1


class StubMigrationRegistry(MigrationRegistry):

    def __init__(self, steps: Iterable[Migration]):
        self._chain = steps
        self.path_calls = []

    def path(self, current: Version, target: Version):
        self.path_calls.append((current, target))
        return self._chain


class StubMigrationStep(Migration):

    def __init__(self, from_v: str, to_v: str, fail=False):
        self.from_version = Version(from_v)
        self.to_version = Version(to_v)
        self.description = f"{from_v} -> {to_v}"

        self.calls = 0
        self.apply_args = None
        self.fail = fail

    def apply(self, config, logger=None):
        self.calls += 1
        self.apply_args = {"config": config, "logger": logger}
        if self.fail:
            raise MigrationRuntimeError(f"Step failed {self.description}")


class StubLogger:
    """
    Captures info messages for assertions.
    """
    def __init__(self):
        self.messages = []

    def info(self, msg):
        self.messages.append(msg)


def test_apply_migrations_runs_all_steps_in_order_and_persists_each():

    cfg = StubConfig("1.0.0")
    s1 = StubMigrationStep(from_v="1.0.0", to_v="1.1.0")
    s2 = StubMigrationStep(from_v="1.1.0", to_v="1.2.0")
    log = StubLogger()
    registry = StubMigrationRegistry([s1, s2])

    apply_migrations(config=cfg, registry=registry, target=Version("1.2.0"), logger=log)

    # Registry was asked for the correct path
    assert registry.path_calls == [(Version("1.0.0"), Version("1.2.0"))]

    # Steps executed exactly once, in order
    assert s1.calls == 1
    assert s2.calls == 1

    # Each apply() received the same config and the logger
    assert s1.apply_args["config"] is cfg and s1.apply_args["logger"] is log
    assert s2.apply_args["config"] is cfg and s2.apply_args["logger"] is log

    # Config version advanced step-by-step and persisted for each step
    assert cfg.migrated_with_version == Version("1.2.0")
    assert cfg._saves == 2  # one save per successful step

    # Check logging: progress + completion
    assert any("Migrating 1.0.0 -> 1.1.0" in m for m in log.messages)
    assert any("Migrating 1.1.0 -> 1.2.0" in m for m in log.messages)
    assert any("Migration complete. Current schema: 1.2.0" in m for m in log.messages)


def test_apply_migrations_noop_when_chain_is_empty():
    """
    If registry.path() returns an empty chain (already at target),
    nothing should be applied, version unchanged, no saves.
    """
    cfg = StubConfig("1.2.0")
    registry = StubMigrationRegistry(steps=[])
    log = StubLogger()

    apply_migrations(config=cfg, registry=registry, target=Version("1.2.0"), logger=log)

    # Still called path; nothing else happened
    assert registry.path_calls == [(Version("1.2.0"), Version("1.2.0"))]
    assert cfg.migrated_with_version == Version("1.2.0")
    assert cfg._saves == 0
    # Only completion log should appear (per your implementation, it logs completion regardless)
    assert any("Migration complete" in m for m in log.messages)


def test_apply_migrations_stops_on_failure_and_persists_only_successful_steps():
    """
    If a step fails, the function should persist only successful steps
    """
    cfg = StubConfig("1.0.0")
    ok = StubMigrationStep("1.0.0", "1.1.0")
    boom = StubMigrationStep("1.1.0", "1.2.0", fail=True)
    registry = StubMigrationRegistry([ok, boom])
    log = StubLogger()

    with pytest.raises(MigrationRuntimeError) as ei:
        apply_migrations(config=cfg, registry=registry, target=Version("1.2.0"), logger=log)
    assert "Step failed" in str(ei.value)

    # First step succeeded and was saved
    assert ok.calls == 1
    assert cfg._saves == 1
    assert cfg.migrated_with_version == Version("1.1.0")

    # Second step attempted and failed; no further saves
    assert boom.calls == 1
