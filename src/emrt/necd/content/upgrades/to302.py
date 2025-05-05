import gc
import logging

import plone.api as api
import transaction

logger = logging.getLogger(__name__)


def get_candidates(brains):
    for brain in brains:
        if not brain.get("text"):
            obj = brain.getObject()
            if getattr(obj, "text", None):
                yield obj


def reindex_observation_text(folder):
    catalog = api.portal.get_tool("portal_catalog")
    candidates = get_candidates(
        catalog(
            portal_type="Observation",
            path="/".join(
                folder.getPhysicalPath(),
            ),
        )
    )
    for idx, obs in enumerate(candidates, start=1):
        logger.info("[%s] Reindexing %s...", idx, obs.absolute_url(1))
        obs.reindexObject(idxs=["text"], update_metadata=True)
        if idx % 4000 == 0:
            logger.info("Collect: %s...", idx)
            gc.collect()
        if idx % 2000 == 0:
            logger.info("Commit: %s...", idx)
            transaction.commit()
        elif idx % 1000 == 0:
            logger.info("Savepoint: %s...", idx)
            transaction.savepoint(optimistic=True)
    logger.info("Done.")
    transaction.commit()


def run(_):
    portal = api.portal.get()
    reindex_observation_text(portal["2025"])
