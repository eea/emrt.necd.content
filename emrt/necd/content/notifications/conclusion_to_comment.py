from Products.CMFCore.WorkflowCore import ActionSucceededEvent
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from emrt.necd.content.constants import ROLE_CP
from emrt.necd.content.constants import ROLE_LR
from emrt.necd.content.notifications.base_notification import (
    BaseWorkflowNotification,
)
from emrt.necd.content.observation import Observation


class Notification(
    BaseWorkflowNotification[Observation, ActionSucceededEvent]
):
    """Base notification."""


class NotificationCP(Notification):
    """To: CounterParts. When: New draft conclusion to comment on."""

    template = ViewPageTemplateFile("conclusion_to_comment.pt")

    subject = "New draft conclusion to comment on"
    action_types = ("request-comments",)
    target_role = ROLE_CP
    notification_name = "conclusion_to_comment"


class NotificationLR(Notification):
    """To: LeadReviewer. When: New draft question to comment on."""

    template = ViewPageTemplateFile("conclusion_to_comment.pt")

    subject = "New draft conclusion to comment on"
    action_types = ("request-comments",)
    target_role = ROLE_LR
    notification_name = "conclusion_to_comment"


notification_cp = NotificationCP.factory
notification_lr = NotificationLR.factory
