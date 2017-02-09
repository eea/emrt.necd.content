from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from Acquisition import aq_parent
from DateTime import DateTime
from emrt.necd.content.comment import IComment
from emrt.necd.content.commentanswer import ICommentAnswer
from emrt.necd.content.observation import IObservation
from emrt.necd.content.question import IQuestion
from five import grok
from plone import api
from Products.CMFCore.interfaces import IActionSucceededEvent
from Products.CMFCore.utils import getToolByName
from zope.lifecycleevent.interfaces import IObjectRemovedEvent


@grok.subscribe(IQuestion, IActionSucceededEvent)
def question_transition(question, event):
    if event.action in ['phase2-approve-question']:
        wf = getToolByName(question, 'portal_workflow')
        comment_id = wf.getInfoFor(question,
            'comments', wf_id='esd-question-review-workflow')
        comment = question.get(comment_id, None)
        if comment is not None:
            comment_state = api.content.get_state(obj=comment)
            comment.setEffectiveDate(DateTime())
            if comment_state in ['initial']:
                api.content.transition(obj=comment, transition='publish')

    if event.action in ['phase2-approve-question']:
        observation = aq_parent(question)
        if api.content.get_state(observation) == 'phase2-draft':
            api.content.transition(obj=observation, transition='phase2-open')

    if event.action in ['phase2-recall-question-lr']:
        wf = getToolByName(question, 'portal_workflow')
        comment_id = wf.getInfoFor(question,
            'comments', wf_id='esd-question-review-workflow')
        comment = question.get(comment_id, None)
        if comment is not None:
            comment_state = api.content.get_state(obj=comment)
            if comment_state in ['public']:
                api.content.transition(obj=comment, transition='retract')

    if event.action in ['phase2-answer-to-lr']:
        wf = getToolByName(question, 'portal_workflow')
        comment_id = wf.getInfoFor(question,
            'comments', wf_id='esd-question-review-workflow')
        comment = question.get(comment_id, None)
        if comment is not None:
            comment_state = api.content.get_state(obj=comment)
            comment.setEffectiveDate(DateTime())
            if comment_state in ['initial']:
                api.content.transition(obj=comment, transition='publish')

    if event.action in ['phase2-recall-msa']:
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


@grok.subscribe(IObservation, IActionSucceededEvent)
def observation_transition(observation, event):

    if event.action == 'phase2-reopen-qa-chat':
        with api.env.adopt_roles(roles=['Manager']):
            qs = [q for q in observation.values() if q.portal_type == 'Question']
            if qs:
                q = qs[0]
                api.content.transition(obj=q, transition='phase2-reopen')

    elif event.action in ['phase2-request-comments']:
        with api.env.adopt_roles(roles=['Manager']):
            conclusions = [c for c in observation.values() if c.portal_type == 'ConclusionsPhase2']
            if conclusions:
                conclusion = conclusions[0]
                api.content.transition(obj=conclusion,
                    transition='request-comments')

    elif event.action in ['phase2-finish-comments']:
        with api.env.adopt_roles(roles=['Manager']):
            conclusions = [c for c in observation.values() if c.portal_type == 'ConclusionsPhase2']
            if conclusions:
                conclusion = conclusions[0]
                api.content.transition(obj=conclusion,
                    transition='redraft')

    elif event.action in ['phase2-finish-observation']:
        with api.env.adopt_roles(roles=['Manager']):
            conclusions = [c for c in observation.values() if c.portal_type == 'ConclusionsPhase2']
            if conclusions:
                conclusion = conclusions[0]
                api.content.transition(obj=conclusion,
                    transition='ask-approval')

    elif event.action in ['phase2-confirm-finishing-observation']:
        with api.env.adopt_roles(roles=['Manager']):
            conclusions = [c for c in observation.values() if c.portal_type == 'ConclusionsPhase2']
            if conclusions:
                conclusion = conclusions[0]
                api.content.transition(obj=conclusion,
                    transition='publish')

    elif event.action in ['phase2-deny-finishing-observation']:
        with api.env.adopt_roles(roles=['Manager']):
            conclusions = [c for c in observation.values() if c.portal_type == 'ConclusionsPhase2']
            if conclusions:
                conclusion = conclusions[0]
                api.content.transition(obj=conclusion,
                    transition='redraft')

    elif event.action == 'phase2-draft-conclusions':
        with api.env.adopt_roles(roles=['Manager']):
            questions = [c for c in observation.values() if c.portal_type == 'Question']
            if questions:
                question = questions[0]
                if api.content.get_state(question) == 'phase2-draft':
                    api.content.transition(obj=question,
                        transition='phase2-close')
                elif api.content.get_state(question) in ['phase2-drafted', 'phase2-recalled-lr']:
                    api.content.transition(obj=question,
                        transition='phase2-close-lr')

    elif event.action == 'recall-from-phase2':
        with api.env.adopt_roles(roles=['Manager']):
            questions = [c for c in observation.values() if c.portal_type == 'Question']
            if questions:
                question = questions[0]
                api.content.transition(
                    obj=question,
                    transition='phase2-recall'
                )

    elif event.action == 'phase2-reopen-closed-observation':
        with api.env.adopt_roles(roles=['Manager']):
            conclusions = [c for c in observation.values() if c.portal_type == 'ConclusionsPhase2']
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

    observation.reindexObject()