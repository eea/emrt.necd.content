from Acquisition import aq_parent
from emrt.necd.content.question import IQuestion
from five import grok
from Products.CMFCore.interfaces import IActionSucceededEvent
from Products.Five.browser.pagetemplatefile import PageTemplateFile
from utils import notify


@grok.subscribe(IQuestion, IActionSucceededEvent)
def notification_mse(context, event):
    """
    To:     MSExperts
    When:   New question for your country
    """
    _temp = PageTemplateFile('answer_to_msexperts.pt')

    if event.action in ['phase2-assign-answerer']:
        observation = aq_parent(context)
        subject = u'New question for your country'
        notify(
            observation,
            _temp,
            subject,
            'MSExpert',
            'answer_to_msexperts'
        )