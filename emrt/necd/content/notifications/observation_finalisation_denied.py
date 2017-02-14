from emrt.necd.content.observation import IObservation
from five import grok
from Products.CMFCore.interfaces import IActionSucceededEvent
from Products.Five.browser.pagetemplatefile import PageTemplateFile
from utils import notify


@grok.subscribe(IObservation, IActionSucceededEvent)
def notification_rev_ph2(context, event):
    """
    To:     ReviewerPhase2
    When:   Observation finalisation denied
    """
    _temp = PageTemplateFile('observation_finalisation_denied.pt')

    if event.action in ['phase2-deny-finishing-observation']:
        observation = context
        subject = u'Observation finalisation denied'
        notify(
            observation,
            _temp,
            subject,
            'ReviewerPhase2',
            'observation_finalisation_denied'
        )