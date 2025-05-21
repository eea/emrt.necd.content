import logging

import plone.api as api
import transaction

logger = logging.getLogger(__name__)


def reindex_observations(folder):
    catalog = api.portal.get_tool("portal_catalog")
    candidates = (
        b.getObject()
        for b in catalog(
            portal_type="Observation",
            path="/".join(
                folder.getPhysicalPath(),
            ),
        )
    )
    for idx, obs in enumerate(candidates, start=1):
        logger.info("[%s] Reindexing %s...", idx, obs.absolute_url(1))
        obs.reindexObject(
            idxs=["observation_sent_to_msc", "observation_sent_to_mse"]
        )
        if idx % 10 == 0:
            logger.info("Commit: %s...", idx)
            transaction.commit()
    logger.info("Done.")
    transaction.commit()


def run(_):
    portal = api.portal.get()
    reindex_observations(portal["2025"])
