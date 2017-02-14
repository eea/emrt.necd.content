from Acquisition import aq_parent
from emrt.necd.content.question import IQuestion
from five import grok
from Products.CMFCore.interfaces import IActionSucceededEvent
from Products.Five.browser.pagetemplatefile import PageTemplateFile
from utils import notify


@grok.subscribe(IQuestion, IActionSucceededEvent)
def notification_ms(context, event):
    """
    To:     MSAuthority
    When:   New question for your country
    """
    _temp = PageTemplateFile('question_to_ms.pt')

    if event.action in ['approve-question']:
        observation = aq_parent(context)
        subject = u'New question for your country'
        notify(
            observation,
            _temp,
            subject,
            role='MSAuthority',
            notification_name='question_to_ms'
        )


@grok.subscribe(IQuestion, IActionSucceededEvent)
def notification_rev_ph2(context, event):
    """
    To:     NECDReviewer
    When:   Your question was sent to MS
    """
    _temp = PageTemplateFile('question_to_ms_rev_msg.pt')

    if event.action in ['approve-question']:
        observation = aq_parent(context)
        subject = u'Your observation was sent to MS'
        notify(
            observation,
            _temp,
            subject,
            role='NECDReviewer',
            notification_name='question_to_ms'
        )
