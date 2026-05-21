from Acquisition import aq_parent
from DateTime import DateTime
from plone import api
from Products.CMFCore.utils import getToolByName

from emrt.necd.content.constants import ROLE_LR
from emrt.necd.content.observation import IObservation
from emrt.necd.content.utils import find_parent_with_interface


def question_transition(question, event):
    if event.action in ['approve-question']:
        wf = getToolByName(question, 'portal_workflow')
        comment_id = wf.getInfoFor(question,
            'comments', wf_id='esd-question-review-workflow')
        comment = question.get(comment_id, None)
        if comment is not None:
            comment_state = api.content.get_state(obj=comment)
            comment.setEffectiveDate(DateTime())
            if comment_state in ['initial']:
                api.content.transition(obj=comment, transition='publish')

    if event.action in ['approve-question']:
        observation = aq_parent(question)
        if api.content.get_state(observation) == 'draft':
            api.content.transition(obj=observation, transition='open')

    if event.action in ['recall-question-lr']:
        wf = getToolByName(question, 'portal_workflow')
        comment_id = wf.getInfoFor(question,
            'comments', wf_id='esd-question-review-workflow')
        comment = question.get(comment_id, None)
        is_question = comment and comment.portal_type == "Comment"
        if is_question:
            comment_state = api.content.get_state(obj=comment)
            if comment_state in ['public']:
                api.content.transition(obj=comment, transition='retract')
        else:
            raise KeyError

    if event.action in ['answer-to-lr']:
        wf = getToolByName(question, 'portal_workflow')
        comment_id = wf.getInfoFor(question,
            'comments', wf_id='esd-question-review-workflow')
        comment = question.get(comment_id, None)
        is_answer = comment and comment.portal_type == "CommentAnswer"
        if is_answer:
            comment_state = api.content.get_state(obj=comment)
            comment.setEffectiveDate(DateTime())
            if comment_state in ['initial']:
                api.content.transition(obj=comment, transition='publish')
        else:
            raise KeyError

    if event.action in ['recall-msa']:
        wf = getToolByName(question, 'portal_workflow')
        comment_id = wf.getInfoFor(question,
            'comments', wf_id='esd-question-review-workflow')
        comment = question.get(comment_id, None)
        if comment is not None:
            comment_state = api.content.get_state(obj=comment)
            if comment_state in ['public']:
                api.content.transition(obj=comment, transition='retract')

    observation = aq_parent(question)
    observation.reindexObject()


def _restore_question_after_reopen(question):
    if api.content.get_state(question) != "closed":
        return

    history = question.workflow_history.get("esd-question-review-workflow", [])
    close_action = None
    for item in reversed(history):
        if item.get("review_state") == "closed":
            close_action = item.get("action")
            break

    if close_action == "close-lr":
        api.content.transition(obj=question, transition="reopen-lr")
    else:
        api.content.transition(obj=question, transition="reopen")


def _close_question_for_conclusions(question):
    state = api.content.get_state(question)
    if state == "draft":
        transition = "close"
    elif state == "drafted":
        transition = "close-lr"
    elif state == "recalled-lr":
        roles = api.user.get_roles(obj=question)
        transition = "close-lr" if ROLE_LR in roles else "close"
    else:
        return

    api.content.transition(obj=question, transition=transition)


def observation_transition(observation, event):
    if event.action == 'reopen-qa-chat':
        with api.env.adopt_roles(roles=['Manager']):
            qs = [q for q in list(observation.values()) if q.portal_type == 'Question']
            if qs:
                q = qs[0]
                _restore_question_after_reopen(q)

    elif event.action in ['request-comments']:
        with api.env.adopt_roles(roles=['Manager']):
            conclusions = [c for c in list(observation.values()) if c.portal_type == 'Conclusions']
            if conclusions:
                conclusion = conclusions[0]
                api.content.transition(obj=conclusion,
                    transition='request-comments')

    elif event.action in ['finish-comments']:
        with api.env.adopt_roles(roles=['Manager']):
            conclusions = [c for c in list(observation.values()) if c.portal_type == 'Conclusions']
            if conclusions:
                conclusion = conclusions[0]
                api.content.transition(obj=conclusion,
                    transition='redraft')

    elif event.action in ['finish-observation', 'recall-lr']:
        with api.env.adopt_roles(roles=['Manager']):
            conclusions = [c for c in list(observation.values()) if c.portal_type == 'Conclusions']
            if conclusions:
                conclusion = conclusions[0]
                api.content.transition(obj=conclusion,
                    transition='ask-approval')

    elif event.action in ['confirm-finishing-observation']:
        with api.env.adopt_roles(roles=['Manager']):
            conclusions = [c for c in list(observation.values()) if c.portal_type == 'Conclusions']
            if conclusions:
                conclusion = conclusions[0]
                api.content.transition(obj=conclusion,
                    transition='publish')

    elif event.action in ['deny-finishing-observation', 'recall-se-conclusions', 'recall-se-conclusions-lr-denied']:
        with api.env.adopt_roles(roles=['Manager']):
            conclusions = [c for c in list(observation.values()) if c.portal_type == 'Conclusions']
            if conclusions:
                conclusion = conclusions[0]
                api.content.transition(obj=conclusion,
                    transition='redraft')

    elif event.action == 'recall-lr-pending':
        with api.env.adopt_roles(roles=['Manager']):
            conclusions = [c for c in list(observation.values()) if c.portal_type == 'Conclusions']
            if conclusions:
                conclusion = conclusions[0]
                if api.content.get_state(conclusion) != 'draft':
                    api.content.transition(
                        obj=conclusion,
                        transition='redraft'
                    )

            questions = [c for c in list(observation.values()) if c.portal_type == 'Question']
            if questions:
                _restore_question_after_reopen(questions[0])

    elif event.action == 'draft-conclusions':
        with api.env.adopt_roles(roles=['Manager']):
            questions = [c for c in list(observation.values()) if c.portal_type == 'Question']
            if questions:
                _close_question_for_conclusions(questions[0])

    elif event.action == 'recall-from':
        with api.env.adopt_roles(roles=['Manager']):
            questions = [c for c in list(observation.values()) if c.portal_type == 'Question']
            if questions:
                question = questions[0]
                api.content.transition(
                    obj=question,
                    transition='recall'
                )

    elif event.action == 'reopen-closed-observation':
        with api.env.adopt_roles(roles=['Manager']):
            conclusions = [c for c in list(observation.values()) if c.portal_type == 'Conclusions']
            if conclusions:
                conclusion = conclusions[0]
                api.content.transition(
                    obj=conclusion,
                    transition='redraft'
                )
                api.content.transition(
                    obj=conclusion,
                    transition='ask-approval'
                )

    if event.action in ['redraft']:
        wf = getToolByName(question, 'portal_workflow')
        comment_id = wf.getInfoFor(question,
            'comments', wf_id='esd-question-review-workflow')
        comment = question.get(comment_id, None)
        if comment is not None:
            comment_state = api.content.get_state(obj=comment)
            if comment_state in ['public']:
                api.content.transition(obj=comment, transition='retract')


    observation.reindexObject()


def new_discussion_comment(comment, event):
    with api.env.adopt_roles(roles=['Manager']):
        observation = find_parent_with_interface(IObservation, comment)
        observation.reindexObject()


def reindex_observation_qa_extract(context, _):
    observation = context.get_observation()
    observation.reindexObject(idxs=['qa_extract'])
