import logging

from Acquisition import aq_parent
from DateTime import DateTime
from plone import api
from plone.api.exc import InvalidParameterError

import transaction


logger = logging.getLogger(__name__)

STALE_STATES = ("expert-comments", "pending-answer-drafting")
REPAIR_TRANSITION = "repair-stale-answer-state"
QUESTION_WORKFLOW = "esd-question-review-workflow"


def _iter_stale_questions():
    catalog = api.portal.get_tool("portal_catalog")
    brains = catalog(
        portal_type="Question",
        review_state=list(STALE_STATES),
    )
    logger.info("Found %s stale-answer-state candidates.", len(brains))
    for brain in brains:
        yield brain.getObject()


def _repair_question(question):
    if api.content.get_state(question) not in STALE_STATES:
        return False

    if not question.unanswered_questions():
        return False

    try:
        api.content.transition(obj=question, transition=REPAIR_TRANSITION)
    except InvalidParameterError:
        _force_pending_state(question)
    question.reindexObject()
    observation = aq_parent(question)
    observation.reindexObject()
    return True


def _force_pending_state(question):
    wf = api.portal.get_tool("portal_workflow")[QUESTION_WORKFLOW]
    wh = question.workflow_history
    wh[QUESTION_WORKFLOW] = tuple(wh[QUESTION_WORKFLOW]) + (
        {
            "comments": "Repair stale carried-over answer state",
            "actor": api.user.get_current().getId(),
            "time": DateTime(),
            "action": REPAIR_TRANSITION,
            "review_state": "pending",
        },
    )
    wf.updateRoleMappingsFor(question)


def run(_):
    repaired = 0
    with api.env.adopt_roles(["Manager"]):
        for idx, question in enumerate(_iter_stale_questions(), start=1):
            if _repair_question(question):
                repaired += 1
                logger.info("Repaired %s", question.absolute_url(1))

            if idx % 50 == 0:
                transaction.commit()

    transaction.commit()
    logger.info("Repaired %s stale-answer-state questions.", repaired)
