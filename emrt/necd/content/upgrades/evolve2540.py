from logging import getLogger

import plone.api as api

from emrt.necd.content.browser.xls_utils import clean_value
from emrt.necd.content.observation import set_title_to_observation

LOGGER = getLogger(__name__)


QUERY = " OR ".join([
    "so2_x000d_",
    "nox_x000d_",
    "nh3_x000d_",
    "nmvoc_x000d_",
    "5_x000d_",
    "bap_x000d_",
    "pahs_x000d_",
    "pcbs_x000d_",
    "hcb_x000d_",
    "cd_x000d_",
    "hg_x000d_",
    "pb_x000d_",
    "f_x000d_",
    "na_x000d_",
    "pm10_x000d_",
    "co_x000d_",
    "bc_x000d_",
    "tsp_x000d_",
])


def clean_iterable_value(obj, name):
    value = getattr(obj, name, [])
    if value:
        setattr(obj, name, [clean_value(v) for v in value])


def clean_values(obj, names):
    for name in names:
        value = getattr(obj, name, None)
        if value:
            setattr(obj, name, clean_value(value))


def run(_):
    catalog = api.portal.get_tool("portal_catalog")
    brains = catalog(portal_type="Observation", SearchableText=QUERY)
    brains_len = len(brains)
    a_tenth = brains_len / 10
    LOGGER.info("Found %s brains.", brains_len)
    observations = (brain.getObject() for brain in brains)
    for idx, observation in enumerate(observations, start=1):
        # clean Observation
        clean_iterable_value(observation, "pollutants")
        clean_iterable_value(observation, "year")
        clean_values(observation, ["text", "nfr_code"])

        # clean Conclusion if it exists
        conclusion = observation.get_conclusion()
        if conclusion:
            clean_values(conclusion, ["text"])

        set_title_to_observation(observation, None)
        # reindex
        observation.reindexObject()

        # log progress
        if a_tenth and idx % a_tenth == 0:
            LOGGER.info("Done %s/%s.", idx, brains_len)
