import logging

import five.intid.intid
import plone.api as api

from emrt.necd.content.browser.carryover import _replace_uuid

logger = logging.getLogger(__name__)

def fix_carried_over_observations(folder):
    for observation in folder.listFolderContents({"portal_type": "Observation"}):
        if hasattr(observation, "carryover_from"):
            logger.info("Fixing %s", observation.absolute_url(1))
            _replace_uuid(observation)
            five.intid.intid.addIntIdSubscriber(observation, None)
            observation.reindexObject()


def run(_):
    portal = api.portal.get()
    target = portal["2025"]
    fix_carried_over_observations(target)
