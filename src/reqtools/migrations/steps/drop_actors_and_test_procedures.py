from packaging.version import Version
from ..base import Migration

from ...specifications import ReleaseManager, normalize


class DropActorsAndTestProceduresFromContentHash(Migration):
    """
    Migration step 0.0.0 -> 0.3.0

    This migration removes 'actors' and 'test_procedures' fields
    from the content hash computation for all requirements.

    Background:
      - In earlier versions, these fields were included in the content hash .
      - This caused every requirement to appear as "modified" when switching to the new content hash  algorithm, which was incorrect.
      - The new content hash excludes these fields to ensure only relevant structural and textual changes trigger version updates.
    """

    from_version = Version("0.0.0")
    to_version   = Version("0.3.0")
    description  = (
        "Remove 'actors' and 'test_procedures' from content hash and recompute all requirement."
    )

    def apply(self, config, logger=None):
        if logger:
            logger.info("Remove 'actors' and 'test_procedures' from content hash and recompute all requirement")

        # Step 1 Load all requirements for current version
        release_manager = ReleaseManager(config=config)
        release = release_manager.load()

        # Step 2: Recompute fingerprints for all existing requirements.
        for req in release.requirements:
            fp, _ = normalize.build_fingerprint(text=req.text,
                                                title=req.title,
                                                conformance=req.conformance,
                                                actors=None,
                                                test_procedures=None)
            req.content_hash = fp
            logger.info(f"Migrated requirement {req.key}, content hash {req.content_hash}")

        # Step 3: Save updated release requirements back to the store.
        release_manager.save(release)

        # Step 4: Check if current release is frozen and update the frozen hash
        if release_manager.is_current_release_frozen():
            config.frozen_hash = normalize.build_fingerprint_release(requirements=release.requirements)
            config.save()
            logger.info(f"Release is frozen. Migrated frozen hash {config.frozen_hash}.")
        else:
            logger.info(f"Release is not frozen. No need to migrate frozen hash.")
        
