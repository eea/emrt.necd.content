from emrt.necd.content.observation import IObservation
from five import grok
from Products.CMFCore.interfaces import IActionSucceededEvent
from Products.Five.browser.pagetemplatefile import PageTemplateFile
from utils import notify
from emrt.necd.content.constants import ROLE_CP
from emrt.necd.content.constants import ROLE_LR

@grok.subscribe(IObservation, IActionSucceededEvent)
def notification_cp(context, event):
    """
    To:     CounterParts
    When:   New draft conclusion to comment on
    """
    _temp = PageTemplateFile('conclusion_to_comment.pt')

    if event.action in ['request-comments']:
        observation = context
        subject = u'New draft conclusion to comment on'
        notify(
            observation,
            _temp,
            subject,
            ROLE_CP,
            'conclusion_to_comment'
        )


@grok.subscribe(IObservation, IActionSucceededEvent)
def notification_lr(context, event):
    """
    To:     LeadReviewer
    When:   New draft question to comment on
    """
    _temp = PageTemplateFile('conclusion_to_comment.pt')

    if event.action in ['request-comments']:
        observation = context
        subject = u'New draft conclusion to comment on'
        notify(
            observation,
            _temp,
            subject,
            ROLE_LR,
            'conclusion_to_comment'
        )
