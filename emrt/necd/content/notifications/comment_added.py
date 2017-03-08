from functools import partial
from Acquisition import aq_parent
from zope.lifecycleevent.interfaces import IObjectAddedEvent
from Products.Five.browser.pagetemplatefile import PageTemplateFile
from five import grok
from plone.app.discussion.interfaces import IComment
import plone.api as api

from emrt.necd.content.observation import IObservation
from emrt.necd.content.notifications.utils import notify
from emrt.necd.content.utils import find_parent_with_interface
from emrt.necd.content.constants import ROLE_MSA
from emrt.necd.content.constants import ROLE_MSE


def user_has_role_in_context(role, context):
    user = api.user.get_current()
    roles = user.getRolesInContext(context)
    return role in roles

FIND_PARENT_OBSERVATION = partial(find_parent_with_interface, IObservation)
USER_IS_MSE = partial(user_has_role_in_context, ROLE_MSE)


@grok.subscribe(IComment, IObjectAddedEvent)
def notification_mse(context, event):
    """
    To:     MSExperts
    When:   New comment from MSExpert for your country
    """
    _temp = PageTemplateFile('comment_to_mse.pt')

    observation = FIND_PARENT_OBSERVATION(context)
    if not USER_IS_MSE(observation):
        return

    subject = u'New comment from MS Expert'
    notify(
        observation,
        _temp,
        subject,
        ROLE_MSE,
        'comment_to_mse'
    )


@grok.subscribe(IComment, IObjectAddedEvent)
def notification_msc(context, event):
    """
    To:     MSAuthority
    When:   New comment from MSExpert for your country
    """
    _temp = PageTemplateFile('comment_to_msa.pt')

    observation = FIND_PARENT_OBSERVATION(context)
    if not USER_IS_MSE(observation):
        return

    subject = u'New comment from MS Expert'
    notify(
        observation,
        _temp,
        subject,
        ROLE_MSA,
        'comment_to_msa'
    )
