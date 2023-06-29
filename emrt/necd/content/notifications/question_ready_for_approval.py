from Products.CMFCore.WorkflowCore import ActionSucceededEvent
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from emrt.necd.content.constants import ROLE_LR
from emrt.necd.content.notifications.base_notification import BaseWorkflowNotification
from emrt.necd.content.question import Question


class NotificationLR(BaseWorkflowNotification[Question, ActionSucceededEvent]):
    """To: LeadReviewer. When: New question for approval."""

    template = ViewPageTemplateFile("question_ready_for_approval.pt")

    subject = "New question for approval"
    action_types = ("send-to-lr",)
    target_role = ROLE_LR
    notification_name = "question_ready_for_approval"


notification_lr = NotificationLR.factory
