import logging

from emrt.necd.content.upgrades.reindex_observations import reindex_observations

logger = logging.getLogger(__name__)

def run(_):
    reindex_observations(logger, ["qa_extract"])
