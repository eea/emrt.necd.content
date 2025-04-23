import logging

import five.intid.intid
import plone.api as api

from emrt.necd.content.browser.carryover import _replace_uuid, catalog_with_children

logger = logging.getLogger(__name__)

def fix_carried_over_observations(folder):
    catalog = api.portal.get_tool("portal_catalog")
    for observation in folder.listFolderContents({"portal_type": "Observation"}):
        if hasattr(observation, "carryover_from"):
            logger.info("Fixing %s", observation.absolute_url(1))
            _replace_uuid(observation)
            catalog_with_children(catalog, observation)


def run(_):
    portal = api.portal.get()
    target = portal["2025"]
    fix_carried_over_observations(target)
