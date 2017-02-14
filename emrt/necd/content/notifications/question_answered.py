from Acquisition import aq_parent
from emrt.necd.content.question import IQuestion
from five import grok
from Products.CMFCore.interfaces import IActionSucceededEvent
from Products.Five.browser.pagetemplatefile import PageTemplateFile
from utils import notify


@grok.subscribe(IQuestion, IActionSucceededEvent)
def notification_lr(context, event):
    """
    To:     LeadReviewer
    When:   New answer from country
    """
    _temp = PageTemplateFile('question_answered_lr_msg.pt')

    if event.action in ['answer-to-lr']:
        observation = aq_parent(context)
        subject = u'New answer from country'
        notify(
            observation,
            _temp,
            subject,
            'LeadReviewer',
            'question_answered'
        )


@grok.subscribe(IQuestion, IActionSucceededEvent)
def notification_rev_ph2(context, event):
    """
    To:     NECDReviewer
    When:   New answer from country
    """
    _temp = PageTemplateFile('question_answered_rev_msg.pt')

    if event.action in ['answer-to-lr']:
        observation = aq_parent(context)
        subject = u'New answer from country'
        notify(
            observation,
            _temp,
            subject,
            'NECDReviewer',
            'question_answered'
        )


@grok.subscribe(IQuestion, IActionSucceededEvent)
def notification_rev_msexperts(context, event):
    """
    To:     MSExperts
    When:   New answer from country
    """
    _temp = PageTemplateFile('question_answered_msexperts_msg.pt')

    if event.action in ['answer-to-lr']:
        observation = aq_parent(context)
        subject = u'New answer from country'
        notify(
            observation,
            _temp,
            subject,
            'MSExpert',
            'question_answered'
        )
