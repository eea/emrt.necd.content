from Products.CMFCore.WorkflowCore import ActionSucceededEvent
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from emrt.necd.content.constants import ROLE_MSE
from emrt.necd.content.notifications.base_notification import BaseNotification
from emrt.necd.content.question import Question


class NotificationMSE(BaseNotification[Question, ActionSucceededEvent]):
    """To: MSExperts. When: New question for your country."""

    template = ViewPageTemplateFile("answer_to_msexperts.pt")

    subject = "New question for your country"
    action_types = ("assign-answerer",)
    target_role = ROLE_MSE
    notification_name = "answer_to_msexperts"

    def should_run(self, event: ActionSucceededEvent, reassign=False):
        """Check if this notification should run."""
        return super().should_run(event) or reassign


notification_mse = NotificationMSE.factory
