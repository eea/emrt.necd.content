from Products.CMFCore.WorkflowCore import ActionSucceededEvent
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from emrt.necd.content.constants import ROLE_SE
from emrt.necd.content.notifications.base_notification import (
    BaseWorkflowNotification,
)
from emrt.necd.content.observation import Observation


class NotificationSE(
    BaseWorkflowNotification[Observation, ActionSucceededEvent]
):
    """To: SectorExpert. When: Observation finalisation denied."""

    template = ViewPageTemplateFile("observation_finalisation_denied.pt")

    subject = "Observation finalisation denied"
    action_types = ("deny-finishing-observation",)
    target_role = ROLE_SE
    notification_name = "observation_finalisation_denied"


notification_se = NotificationSE.factory
