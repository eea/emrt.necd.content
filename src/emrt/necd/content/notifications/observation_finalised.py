from Products.CMFCore.WorkflowCore import ActionSucceededEvent
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from emrt.necd.content.constants import ROLE_MSA
from emrt.necd.content.constants import ROLE_SE
from emrt.necd.content.notifications.base_notification import (
    BaseWorkflowNotification,
)
from emrt.necd.content.observation import Observation


class Notification(
    BaseWorkflowNotification[Observation, ActionSucceededEvent]
):
    """Base notification."""


class NotificationMS(Notification):
    """To: MSAuthority. When: Observation was finalised."""

    template = ViewPageTemplateFile("observation_finalised.pt")

    subject = "An observation for your country was finalised"
    action_types = ("confirm-finishing-observation",)
    target_role = ROLE_MSA
    notification_name = "observation_finalised"


class NotificationSE(Notification):
    """To: SectorExpert. When: Observation finalised."""

    template = ViewPageTemplateFile("observation_finalised_rev_msg.pt")

    subject = "Your observation was finalised"
    action_types = ("confirm-finishing-observation",)
    target_role = ROLE_SE
    notification_name = "observation_finalised"


notification_ms = NotificationMS.factory
notification_se = NotificationSE.factory
