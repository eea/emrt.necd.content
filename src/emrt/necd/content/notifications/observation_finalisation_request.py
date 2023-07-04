from Products.CMFCore.WorkflowCore import ActionSucceededEvent
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from emrt.necd.content.constants import ROLE_LR
from emrt.necd.content.notifications.base_notification import (
    BaseWorkflowNotification,
)
from emrt.necd.content.observation import Observation


class NotificationLR(
    BaseWorkflowNotification[Observation, ActionSucceededEvent]
):
    """To: LeadReviewer. When: Observation finalisation request."""

    template = ViewPageTemplateFile("observation_finalisation_request.pt")

    subject = "Observation finalisation request"
    action_types = ("finish-observation",)
    target_role = ROLE_LR
    notification_name = "observation_finalisation_request"


notification_lr = NotificationLR.factory
