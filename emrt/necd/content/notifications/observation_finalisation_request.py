from emrt.necd.content.observation import IObservation
from five import grok
from Products.CMFCore.interfaces import IActionSucceededEvent
from Products.Five.browser.pagetemplatefile import PageTemplateFile
from utils import notify


@grok.subscribe(IObservation, IActionSucceededEvent)
def notification_lr(context, event):
    """
    To:     LeadReviewer
    When:   Observation finalisation request
    """
    _temp = PageTemplateFile('observation_finalisation_request.pt')

    if event.action in ['phase2-finish-observation']:
        observation = context
        subject = u'Observation finalisation request'
        notify(
            observation,
            _temp,
            subject,
            'LeadReviewer',
            'observation_finalisation_request'
        )