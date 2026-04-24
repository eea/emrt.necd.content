from Products.CMFCore.WorkflowCore import ActionSucceededEvent
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from emrt.necd.content.constants import ROLE_SE
from emrt.necd.content.notifications.base_notification import (
    BaseWorkflowNotification,
)
from emrt.necd.content.question import Question


class NotificationSE(BaseWorkflowNotification[Question, ActionSucceededEvent]):
    """To: SectorExpert. When: Redraft requested by LR."""

    template = ViewPageTemplateFile("question_redraft.pt")

    subject = "Redraft requested."
    action_types = ("redraft",)
    target_role = ROLE_SE
    notification_name = "question_redraft"


notification_se = NotificationSE.factory
