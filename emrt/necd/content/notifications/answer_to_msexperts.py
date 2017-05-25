from Acquisition import aq_parent
from emrt.necd.content.question import IQuestion
from five import grok
from Products.CMFCore.interfaces import IActionSucceededEvent
from Products.Five.browser.pagetemplatefile import PageTemplateFile
from utils import notify
from emrt.necd.content.constants import ROLE_MSE


@grok.subscribe(IQuestion, IActionSucceededEvent)
def notification_mse(context, event=None, reassign=False):
    """
    To:     MSExperts
    When:   New question for your country
    """
    _temp = PageTemplateFile('answer_to_msexperts.pt')

    should_run = (
        event
        and event.action in ['assign-answerer']
        or reassign
    )

    if should_run:
        observation = aq_parent(context)
        subject = u'New question for your country'
        notify(
            observation,
            _temp,
            subject,
            ROLE_MSE,
            'answer_to_msexperts'
        )
