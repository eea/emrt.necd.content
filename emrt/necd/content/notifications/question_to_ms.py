from Products.CMFCore.WorkflowCore import ActionSucceededEvent
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from emrt.necd.content.constants import ROLE_MSA
from emrt.necd.content.constants import ROLE_SE
from emrt.necd.content.notifications.base_notification import BaseNotification
from emrt.necd.content.question import Question


class NotificationMS(BaseNotification[Question, ActionSucceededEvent]):
    """To: MSAuthority. When: New question for your country."""

    template = ViewPageTemplateFile("question_to_ms.pt")

    subject = "New question for your country"
    action_types = ("approve-question",)
    target_role = ROLE_MSA
    notification_name = "question_to_ms"


class NotificationSE(BaseNotification[Question, ActionSucceededEvent]):
    """To: SectorExpert. When: Your question was sent to MS."""

    template = ViewPageTemplateFile("question_to_ms_rev_msg.pt")

    subject = "Your observation was sent to MS"
    action_types = ("approve-question",)
    target_role = ROLE_SE
    notification_name = "question_to_ms"


notification_ms = NotificationMS.factory
notification_se = NotificationSE.factory
