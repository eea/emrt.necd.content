from Products.CMFCore.WorkflowCore import ActionSucceededEvent
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from emrt.necd.content.constants import ROLE_CP
from emrt.necd.content.constants import ROLE_LR
from emrt.necd.content.notifications.base_notification import BaseWorkflowNotification
from emrt.necd.content.question import Question


class NotificationCP(BaseWorkflowNotification[Question, ActionSucceededEvent]):
    """To: CounterParts. When: New draft question to comment on."""

    template = ViewPageTemplateFile("question_to_counterpart.pt")

    subject = "New draft question to comment"
    action_types = ("request-for-counterpart-comments",)
    target_role = ROLE_CP
    notification_name = "question_to_counterpart"

    def should_run(self, event: ActionSucceededEvent, reassign=False):
        """Check if this notification should run."""
        return super().should_run(event) or reassign


class NotificationLR(BaseWorkflowNotification[Question, ActionSucceededEvent]):
    """To: LeadReviewer. When: New draft question to comment on."""

    template = ViewPageTemplateFile("question_to_counterpart.pt")

    subject = "New draft question to comment"
    action_types = ("request-for-counterpart-comments",)
    target_role = ROLE_LR
    notification_name = "question_to_counterpart"


notification_cp = NotificationCP.factory
notification_lr = NotificationLR.factory
