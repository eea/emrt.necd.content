from Products.CMFCore.WorkflowCore import ActionSucceededEvent
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from emrt.necd.content.constants import ROLE_LR
from emrt.necd.content.constants import ROLE_MSE
from emrt.necd.content.constants import ROLE_SE
from emrt.necd.content.notifications.base_notification import BaseNotification
from emrt.necd.content.question import Question


class NotificationLR(BaseNotification[Question, ActionSucceededEvent]):
    """To: LeadReviewer. When: New answer from country."""

    template = ViewPageTemplateFile("question_answered_lr_msg.pt")

    subject = "New answer from country"
    action_types = ("answer-to-lr",)
    target_role = ROLE_LR
    notification_name = "question_answered"


class NotificationSE(BaseNotification[Question, ActionSucceededEvent]):
    """To: SectorExpert. When: New answer from country."""

    template = ViewPageTemplateFile("question_answered_rev_msg.pt")

    subject = "New answer from country"
    action_types = ("answer-to-lr",)
    target_role = ROLE_SE
    notification_name = "question_answered"


class NotificationRevMSE(BaseNotification[Question, ActionSucceededEvent]):
    """To: MSExperts. When: New answer from country."""

    template = ViewPageTemplateFile("question_answered_msexperts_msg.pt")

    subject = "New answer from country"
    action_types = ("answer-to-lr",)
    target_role = ROLE_MSE
    notification_name = "question_answered"


notification_lr = NotificationLR.factory
notification_se = NotificationSE.factory
notification_rev_msexperts = NotificationRevMSE.factory
