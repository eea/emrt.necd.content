import logging
from functools import lru_cache
from typing import Generic
from typing import Optional
from typing import Tuple
from typing import Type
from typing import TypeVar
from typing import cast

from OFS.Traversable import Traversable

from zope.interface.interfaces import ObjectEvent

from Products.CMFCore.WorkflowCore import WorkflowActionEvent
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone import api
from plone.dexterity.content import DexterityContent

from emrt.necd.content.constants import VALID_ROLES
from emrt.necd.content.observation import IObservation
from emrt.necd.content.observation import Observation
from emrt.necd.content.utils import find_parent_with_interface

from .utils import notify

logger = logging.getLogger(__name__)

T = TypeVar("T", bound="BaseNotification")

Context = TypeVar("Context", bound=Traversable)
Event = TypeVar("Event", bound=ObjectEvent)

WorkflowContext = TypeVar("WorkflowContext", bound=DexterityContent)
WorkflowEvent = TypeVar("WorkflowEvent", bound=WorkflowActionEvent)


class BaseNotification(BrowserView, Generic[Context, Event]):
    """Base class for notifications."""

    context: Context
    template: ViewPageTemplateFile

    subject: str

    target_role: VALID_ROLES
    notification_name: str

    def __call__(self, event: Event, **kwargs):
        """Send notification."""
        if self.should_run(event, **kwargs):
            self.run()

    def should_run(self, event: Event, **kwargs):
        """Check if this notification should run."""
        return NotImplemented

    @lru_cache
    def get_observation(self) -> Optional[Observation]:
        """Get the parent observation."""
        return cast(
            Optional[Observation],
            find_parent_with_interface(
                IObservation,
                self.context,
            ),
        )

    def run(self):
        """Run notification."""
        observation = self.get_observation()
        if observation:
            notify(
                observation,
                self.template,
                self.subject,
                self.target_role,
                self.notification_name,
            )
        else:
            logger.warn("Could not locate observation for {self.__class__}!")

    @classmethod
    def factory(cls: Type[T], context: Context, event: Event, **kwargs):
        """Instantiate the class and call it."""
        return cls(context, api.env.getRequest())(event, **kwargs)


class BaseWorkflowNotification(
    BaseNotification[WorkflowContext, WorkflowEvent]
):
    """Base notification class for workflow-related notifications."""

    action_types: Tuple[str]

    def should_run(self, event: WorkflowEvent, **kwargs):
        """Check if this notification should run."""
        return event.action in self.action_types


class BaseContentNotification(BaseNotification[Context, Event]):
    """Base notification class for comment notifications."""
