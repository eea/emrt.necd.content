from logging import getLogger

import transaction

from zope.component import getMultiAdapter
from zope.globalrequest import getRequest

import plone.api as api


LOGGER = getLogger(__name__)


def filter_is_carried_over(obs):
    return hasattr(obs, "carryover_from")


def filter_has_comments(obs):
    return (
        getattr(obs, "closing_comments", None)
        or getattr(obs, "closing_deny_comments", None)
    )

def run(_):
    catalog = api.portal.get_tool("portal_catalog")
    brains = catalog(portal_type="Observation")
    brains_len = len(brains)
    a_tenth = brains_len / 10
    observations = (brain.getObject() for brain in brains)
    LOGGER.info("Found %s brains. Selecting some...", brains_len)
    valid_observations = (
        obj
        for obj in observations
        if filter_is_carried_over(obj) and filter_has_comments(obj)
    )
    request = getRequest()
    for idx, observation in enumerate(valid_observations, start=1):
        LOGGER.info(observation.absolute_url(1))

        observation_view = getMultiAdapter((observation, request), name="view")
        carryover_source = observation_view.carryover_source()

        if not carryover_source:
            continue

        if getattr(observation, "closing_comments", None) == getattr(
            carryover_source, "closing_comments", None
        ):
            observation.closing_comments = u""

        if getattr(observation, "closing_deny_comments", None) == getattr(
            carryover_source, "closing_deny_comments", None
        ):
            observation.closing_deny_comments = u""

        # log progress
        if a_tenth and idx % a_tenth == 0:
            transaction.savepoint(optimistic=True)
            LOGGER.info("Done %s/ < %s.", idx, brains_len)
