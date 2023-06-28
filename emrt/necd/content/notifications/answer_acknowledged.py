from Products.CMFCore.WorkflowCore import ActionSucceededEvent
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from emrt.necd.content.constants import ROLE_MSA
from emrt.necd.content.notifications.base_notification import BaseNotification
from emrt.necd.content.question import Question


class NotificationLR(BaseNotification[Question, ActionSucceededEvent]):
    """To: MSAuthority. When: Answer Acknowledged."""

    template = ViewPageTemplateFile("answer_acknowledged.pt")

    subject = "Your answer was acknowledged"
    action_types = ("validate-answer-msa",)
    target_role = ROLE_MSA
    notification_name = "answer_acknowledged"


notification_lr = NotificationLR.factory
