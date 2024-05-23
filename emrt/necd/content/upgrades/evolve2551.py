from logging import getLogger

import transaction
from DateTime import DateTime

import plone.api as api


LOGGER = getLogger(__name__)


def run(_):
    catalog = api.portal.get_tool("portal_catalog")
    brains = catalog(portal_type="Observation", modified={"range": "min", "query": DateTime("2024/02/19")})

    brains_len = len(brains)
    a_tenth = brains_len / 10

    LOGGER.info("Found %s brains...", brains_len)

    observations = (b.getObject() for b in brains)

    for idx, observation in enumerate(observations, start=1):
        LOGGER.info(observation.absolute_url(1))

        observation.reindexObject()

        # log progress
        if a_tenth and idx % a_tenth == 0:
            transaction.savepoint(optimistic=True)
            LOGGER.info("Done %s/%s.", idx, brains_len)
