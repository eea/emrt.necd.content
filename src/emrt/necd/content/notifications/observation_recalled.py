from functools import lru_cache
from typing import Literal
from typing import Tuple

from Products.CMFCore.WorkflowCore import ActionSucceededEvent
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from emrt.necd.content.constants import ROLE_MSA
from emrt.necd.content.constants import ROLE_SE
from emrt.necd.content.notifications.base_notification import (
    BaseWorkflowNotification,
)
from emrt.necd.content.observation import Observation

OBS_STATES = {
    "closed": "closed",
    "conclusions-lr-denied": "denied",
}


class Notification(
    BaseWorkflowNotification[Observation, ActionSucceededEvent]
):
    """Base notification."""

    template_suffix: Literal["msa", "se"]
    for_prev_states: Tuple[str, ...]

    action_types = ("recall-lr",)
    notification_name = "observation_recalled"

    @property
    def subject(self):
        """The subject depends on the previous state."""
        return f"A {self.get_prev_state()} observation was recalled"

    @property
    def template(self):
        """The template used depends on the previous state."""
        return ViewPageTemplateFile(
            f"observation_recalled_{self.get_prev_state()}_{self.template_suffix}.pt"
        )

    def should_run(self, event: ActionSucceededEvent, **kwargs):
        """Check if this notification should run."""
        pass_super = super().should_run(event, **kwargs)
        return pass_super and self.get_prev_state() in self.for_prev_states

    @lru_cache
    def get_prev_state(self):
        """Get previous state."""
        prev_wf_state = self.get_observation().workflow_history.get(
            "esd-review-workflow"
        )[-2]["review_state"]
        return OBS_STATES[prev_wf_state]


class NotificationMS(Notification):
    """To: MSAuthority. When: Observation was recalled."""

    target_role = ROLE_MSA
    for_prev_states = ("closed",)
    template_suffix = "msa"


class NotificationSE(Notification):
    """To: SectorExpert. When: Observation was recalled."""

    target_role = ROLE_SE
    for_prev_states = (
        "closed",
        "denied",
    )
    template_suffix = "se"


notification_ms = NotificationMS.factory
notification_se = NotificationSE.factory
