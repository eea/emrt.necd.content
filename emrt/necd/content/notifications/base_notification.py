from typing import Generic
from typing import Tuple
from typing import TypeVar, Type
from typing import cast

from Acquisition import aq_parent

from Products.CMFCore.WorkflowCore import WorkflowActionEvent
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone import api
from plone.dexterity.content import DexterityContent

from emrt.necd.content.constants import VALID_ROLES
from emrt.necd.content.observation import Observation

from .utils import notify

T = TypeVar("T", bound="BaseNotification")

Context = TypeVar("Context", bound=DexterityContent)
Event = TypeVar("Event", bound=WorkflowActionEvent)


class BaseNotification(BrowserView, Generic[Context, Event]):
    """To: LeadReviewer. When: New question for approval."""

    context: Context
    template: ViewPageTemplateFile

    subject: str
    action_types: Tuple[str]
    target_role: VALID_ROLES
    notification_name: str

    def __call__(self, event: Event, **kwargs):
        """Send notification."""
        if self.should_run(event, **kwargs):
            observation = self.get_observation()
            subject = self.subject
            notify(
                observation,
                self.template,
                subject,
                self.target_role,
                self.notification_name,
            )

    def should_run(self, event: Event, **kwargs):
        """Check if this notification should run."""
        return event.action in self.action_types

    def get_observation(self) -> Observation:
        """Get the parent observation."""
        return cast(Observation, aq_parent(self.context))

    @classmethod
    def factory(cls: Type[T], context: Context, event: Event, **kwargs):
        """Instantiate the class and call it."""
        return cls(context, api.env.getRequest())(event, **kwargs)
