from functools import partial
from itertools import chain
from typing import Tuple

from zope.lifecycleevent import ObjectAddedEvent

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone import api
from plone.app.discussion.comment import Comment

from emrt.necd.content.constants import ROLE_CP
from emrt.necd.content.constants import ROLE_LR
from emrt.necd.content.constants import ROLE_MSA
from emrt.necd.content.constants import ROLE_MSE
from emrt.necd.content.constants import ROLE_SE
from emrt.necd.content.constants import VALID_ROLES
from emrt.necd.content.notifications import utils
from emrt.necd.content.notifications.base_notification import (
    BaseContentNotification,
)
from emrt.necd.content.observation import IObservation
from emrt.necd.content.utils import find_parent_with_interface


def user_has_role_in_context(role, context):
    """Check the current user for the specified role in the given context."""
    user = api.user.get_current()
    roles = user.getRolesInContext(context)
    return role in roles


def run_rolecheck(context, func):
    """Runs the `func` checker in the given `context`.

    `func` is a `user_has_role_in_context` partial.
    (e.g. run_rolecheck(observation, USER_IS_SE)).
    """
    return func(context)


PARENT_OBSERVATION = partial(find_parent_with_interface, IObservation)
USER_IS_MSE = partial(user_has_role_in_context, ROLE_MSE)
USER_IS_SE = partial(user_has_role_in_context, ROLE_SE)
USER_IS_CP = partial(user_has_role_in_context, ROLE_CP)
USER_IS_LR = partial(user_has_role_in_context, ROLE_LR)


class Notification(BaseContentNotification[Comment, ObjectAddedEvent]):
    """Base notification."""


class NotificationMSE(Notification):
    """To: MSExperts. When: New comment from MSExpert for your country."""

    template = ViewPageTemplateFile("comment_to_mse.pt")

    subject = "New comment from MS Expert"

    target_role = ROLE_MSE
    notification_name = "comment_to_mse"

    def should_run(self, event: ObjectAddedEvent, **kwargs):
        """Check if this notification should run."""
        observation = self.get_observation()
        return USER_IS_MSE(observation)


notification_mse = NotificationMSE.factory


class NotificationMSA(Notification):
    """To: MSAuthority. When: New comment from MSExpert for your country."""

    template = ViewPageTemplateFile("comment_to_msa.pt")

    subject = "New comment from MS Expert"

    target_role = ROLE_MSA
    notification_name = "comment_to_msa"

    def should_run(self, event: ObjectAddedEvent, **kwargs):
        """Check if this notification should run."""
        observation = self.get_observation()
        return USER_IS_MSE(observation)


notification_msa = NotificationMSA.factory


class NotificationUsers(Notification):
    """To: SectorExpert / CounterPart / LeadReviewer. When: New comment.

    This is a single handler because a user might have multiple roles
    (e.g. CounterPart and SectorExpert, resulting in duplicate emails.
    """

    template = ViewPageTemplateFile("new_comment.pt")
    subject = "New comment"

    notification_name = "new_comment"

    taget_roles: Tuple[VALID_ROLES, ...] = (ROLE_CP, ROLE_SE, ROLE_LR)

    def should_run(self, event: ObjectAddedEvent, **kwargs):
        """Check if this notification should run."""
        observation = self.get_observation()
        checker = partial(run_rolecheck, observation)

        has_valid_roles = list(
            map(checker, (USER_IS_SE, USER_IS_CP, USER_IS_LR))
        )
        return any(has_valid_roles)

    def run(self):
        """Run notification."""
        current_user = api.user.get_current()
        observation = self.get_observation()
        get_obs_users = partial(utils.get_users_in_context, observation)

        def get_users(role):
            return get_obs_users(role, self.notification_name)

        def not_current(user):
            return user != current_user

        users = tuple(
            filter(
                not_current,
                set(chain(*list(map(get_users, self.taget_roles)))),
            )
        )

        content = self.template(**dict(observation=observation))

        utils.send_mail(self.subject, utils.safe_text(content), users)


notify_users = NotificationUsers.factory
