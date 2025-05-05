import logging

import plone.api as api
import transaction

logger = logging.getLogger(__name__)


def get_candidates(brains):
    for brain in brains:
        if not brain.get("text"):
            yield brain.getObject()


def reindex_observation_text():
    catalog = api.portal.get_tool("portal_catalog")
    candidates = get_candidates(catalog(portal_type="Observation"))
    for idx, obs in enumerate(candidates, start=1):
        logger.info("[%s] Reindexing %s...", idx, obs.absolute_url(1))
        obs.reindexObject()
        if idx % 2000 == 0:
            logger.info("Commit: %s...", idx)
            transaction.commit()
        elif idx % 1000 == 0:
            logger.info("Savepoint: %s...", idx)
            transaction.savepoint(optimistic=True)
    transaction.commit()


def run(_):
    reindex_observation_text()
