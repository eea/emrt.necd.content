import logging

import plone.api as api
import transaction

logger = logging.getLogger(__name__)


def get_questions(obs):
     return obs.listFolderContents({"portal_type": "Question"})


def get_candidates(brains):
    for brain in brains:
        obj = brain.getObject()
        num_questions = len(get_questions(obj))
        if num_questions > 1:
            yield obj


def fix_observations(folder):
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
        logger.info("[%s] Fixing %s...", idx, obs.absolute_url(1))
        questions = get_questions(obs)
        logger.info("...deleting: %s...", [x.getId() for x in questions[1:]])
        api.content.delete(objects=questions[1:])
        obs.reindexObject()
        if idx % 10 == 0:
            logger.info("Commit: %s...", idx)
            transaction.commit()
    logger.info("Done.")
    transaction.commit()


def run(_):
    portal = api.portal.get()
    fix_observations(portal["2025"])
    fix_observations(portal["2025-projection"])
