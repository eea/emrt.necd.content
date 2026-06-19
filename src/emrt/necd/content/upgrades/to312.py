import datetime
import logging
import time

from plone import api

import transaction

from emrt.necd.content.ms_visibility import observation_already_replied
from emrt.necd.content.ms_visibility import observation_was_sent_to_msc
from emrt.necd.content.ms_visibility import observation_was_sent_to_mse
from emrt.necd.content.review_state import get_review_cycle_year


logger = logging.getLogger(__name__)
BATCH_SIZE = 250

INDEXES = [
    "observation_sent_to_msc",
    "observation_sent_to_mse",
    "observation_already_replied",
]


class MSVisibilityRecord:
    def __init__(
        self,
        observation_sent_to_msc,
        observation_sent_to_mse,
        observation_already_replied,
    ):
        self.observation_sent_to_msc = observation_sent_to_msc
        self.observation_sent_to_mse = observation_sent_to_mse
        self.observation_already_replied = observation_already_replied


def _visibility_record(observation):
    return MSVisibilityRecord(
        observation_sent_to_msc=observation_was_sent_to_msc(observation),
        observation_sent_to_mse=observation_was_sent_to_mse(observation),
        observation_already_replied=observation_already_replied(observation),
    )


def _non_current_review_folder_paths(catalog):
    current_year = datetime.datetime.now().year
    paths = []
    for brain in catalog(portal_type="ReviewFolder"):
        folder = brain.getObject()
        if get_review_cycle_year(folder) != current_year:
            paths.append(brain.getPath())

    return paths


def _candidate_paths(catalog, folder_paths):
    question_candidates = set()
    stale_true_candidates = set()
    observation_brains = {}

    for folder_path in folder_paths:
        for brain in catalog(portal_type="Observation", path=folder_path):
            observation_brains[brain.getPath()] = brain

        for brain in catalog(portal_type="Question", path=folder_path):
            observation_path = brain.getPath().rsplit("/", 1)[0]
            if observation_path in observation_brains:
                question_candidates.add(observation_path)

        for index in INDEXES:
            query = {
                "portal_type": "Observation",
                "path": folder_path,
                index: True,
            }
            for brain in catalog(**query):
                stale_true_candidates.add(brain.getPath())
                observation_brains[brain.getPath()] = brain

    paths = question_candidates | stale_true_candidates
    return paths, question_candidates, stale_true_candidates, observation_brains


def _update_ms_visibility(catalog, observation, path):
    zcatalog = catalog._catalog
    rid = zcatalog.uids[path]
    record = _visibility_record(observation)

    zcatalog.catalogObject(
        record,
        path,
        idxs=INDEXES,
        update_metadata=False,
    )

    metadata = list(zcatalog.data[rid])
    for name in INDEXES:
        metadata[zcatalog.schema[name]] = getattr(record, name)
    zcatalog.data[rid] = tuple(metadata)


def run(_):
    catalog = api.portal.get_tool("portal_catalog")

    with api.env.adopt_roles(["Manager"]):
        folder_paths = _non_current_review_folder_paths(catalog)
        logger.info(
            "Selected %s non-current review folders for MS visibility reindex.",
            len(folder_paths),
        )

        (
            paths,
            question_candidates,
            stale_true_candidates,
            observation_brains,
        ) = _candidate_paths(catalog, folder_paths)
        total = len(paths)
        logger.info(
            "Selected %s question-backed candidates and %s stale-true "
            "candidates; %s total observations to reindex.",
            len(question_candidates),
            len(stale_true_candidates),
            total,
        )

        started = time.monotonic()

        for idx, path in enumerate(sorted(paths), start=1):
            brain = observation_brains[path]
            observation = brain.getObject()
            _update_ms_visibility(catalog, observation, path)

            if idx % BATCH_SIZE == 0:
                elapsed = time.monotonic() - started
                remaining = int((elapsed / idx) * (total - idx))
                logger.info(
                    "Reindexed %s/%s observations. ETA: %ss.",
                    idx,
                    total,
                    remaining,
                )
                transaction.commit()

    transaction.commit()
    logger.info("Finished reindexing MS visibility.")
