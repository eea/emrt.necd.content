import logging

import plone.api as api
import transaction

from emrt.necd.content.browser.carryover import _replace_uuid, catalog_with_children

logger = logging.getLogger(__name__)


def fix_carried_over_observations(folder):
    catalog = api.portal.get_tool("portal_catalog")
    count = 0
    for observation in folder.listFolderContents({"portal_type": "Observation"}):
        if hasattr(observation, "carryover_from"):
            count += 1
            logger.info("Fixing %s", observation.absolute_url(1))
            _replace_uuid(observation)
            catalog_with_children(catalog, observation)
            if count % 10 == 0:
                transaction.savepoint(optimistic=True)


def run(_):
    portal = api.portal.get()
    target = portal["2025"]
    fix_carried_over_observations(target)
