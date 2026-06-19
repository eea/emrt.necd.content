from plone import api

from emrt.necd.content.review_state import get_review_cycle_year


QUESTION_WORKFLOW_ID = "esd-question-review-workflow"


def _item_year(item):
    value = item.get("time")
    year = getattr(value, "year", None)
    return year() if callable(year) else year


def _review_cycle_question_states(context, question):
    review_cycle_year = get_review_cycle_year(context)
    return [
        item.get("review_state")
        for item in question.workflow_history.get(QUESTION_WORKFLOW_ID, [])
        if _item_year(item) == review_cycle_year
    ]


def _first_question(context):
    questions = context.get_values_cat(["Question"])
    return questions[0] if questions else None


def _has_public_question_text(question):
    return any(
        api.content.get_state(obj=item) == "public"
        for item in question.get_questions()
    )


def observation_was_sent_to_msc(context):
    question = _first_question(context)
    if question is None:
        return False

    states = _review_cycle_question_states(context, question)
    was_or_is_pending = any(
        state and state.endswith("pending") for state in states
    )
    return was_or_is_pending and _has_public_question_text(question)


def observation_was_sent_to_mse(context):
    question = _first_question(context)
    if question is None:
        return False

    states = _review_cycle_question_states(context, question)
    return any(
        state and state.endswith("expert-comments") for state in states
    )


def observation_already_replied(context):
    question = _first_question(context)
    if question is None:
        return False

    states = _review_cycle_question_states(context, question)
    if not states:
        return False

    state_positions = {state: idx for idx, state in enumerate(states)}
    return states[-1] not in [
        "recalled-msa",
        "pending",
        "pending-answer-drafting",
        "expert-comments",
    ] and state_positions.get("answered")
