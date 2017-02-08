from emrt.necd.content.observation import IObservation
from five import grok
from Products.CMFCore.interfaces import IActionSucceededEvent
from Products.Five.browser.pagetemplatefile import PageTemplateFile
from utils import notify


@grok.subscribe(IObservation, IActionSucceededEvent)
def notification_ms(context, event):
    """
    To:     MSAuthority
    When:   Observation was finalised
    """
    _temp = PageTemplateFile('observation_finalised.pt')
    if event.action in ['phase2-confirm-finishing-observation']:
        observation = context
        subject = u'An observation for your country was finalised'
        notify(
            observation,
            _temp,
            subject,
            'MSAuthority',
            'observation_finalised'
        )


@grok.subscribe(IObservation, IActionSucceededEvent)
def notification_rev_ph2(context, event):
    """
    To:     ReviewerPhase2
    When:   Observation finalised
    """
    _temp = PageTemplateFile('observation_finalised_rev_msg.pt')
    if event.action in ['phase2-confirm-finishing-observation']:
        observation = context
        subject = u'Your observation was finalised'
        notify(
            observation,
            _temp,
            subject,
            'ReviewerPhase2',
            'observation_finalised'
        )
