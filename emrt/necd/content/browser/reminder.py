import os
from operator import attrgetter
from collections import namedtuple

from zope.component import getMultiAdapter

from chameleon.zpt.template import PageTextTemplate

from Products.Five.browser import BrowserView


import plone.api as api
import plone.memoize

from emrt.necd.content.notifications.utils import get_users_in_context
from emrt.necd.content.notifications.utils import send_mail
from emrt.necd.content.notifications.utils import get_email_context
from emrt.necd.content.notifications.utils import extract_emails
from emrt.necd.content.utils import safer_unicode
from emrt.necd.content.constants import ROLE_MSA


DEFAULT_CONTENT_PATH = os.path.join(
    os.path.dirname(__file__),
    "templates", "reminder_default_content.pt",
)


DEFAULT_CONTENT = ""


with open(DEFAULT_CONTENT_PATH) as default_content:
    DEFAULT_CONTENT = default_content.read()



UserData = namedtuple("UserData", ["name", "email", "roles"])


class ReminderView(BrowserView):

    known_parameters = (
        ("username", "The receiving user's name.", ),
        ("tool_url", "The absolute URL of this review folder.", ),
    )

    @property
    def default_content(self):
        return DEFAULT_CONTENT

    @property
    def default_subject(self):
        return "{} Outstanding questions reminder".format(
            get_email_context(self.context.type)
        )

    @property
    def will_notify_num_users(self):
        return len(self._get_users_to_notify())

    @property
    def manager_users_to_notify(self):
        if "Manager" in api.user.get_roles():
            result = []
            for user in self._get_users_to_notify():
                roles = api.user.get_roles(user=user, obj=self.context)
                user_data = (
                    safer_unicode(user.getProperty("fullname", user.getId())),
                    user.getProperty("email", "-"),
                    [r for r in roles if r != "Authenticated"],
                )
                result.append(UserData(*user_data))
            return sorted(result, key=attrgetter("name"))


    def send_reminder(self):
        subject = self.request.get("subject", self.default_subject)
        content = self.request.get("content", self.default_content)

        template = PageTextTemplate(content)

        to_notify = self._get_users_to_notify()

        for user in to_notify:
            self._send_email(subject, template, user)

        portal_message = "Notified {} users.".format(len(to_notify))
        api.portal.show_message(portal_message, request=self.request)

        return self.request.RESPONSE.redirect(self.context.absolute_url())

    def _send_email(self, subject, template, user):
        params = dict(
            username=safer_unicode(user.getProperty("fullname", user.getId())),
            tool_url=self.context.absolute_url(),
        )

        body = template.render(**params)

        send_mail(subject, body, [user])


    @plone.memoize.view.memoize
    def _get_users_to_notify(self):
        view = getMultiAdapter((self.context, self.request), name="inboxview")
        view()  # initializes view.rolemap_observations

        observations = view.get_observations(
            observation_question_status=[
                'pending',
                'recalled-msa',
                'pending-answer-drafting'
            ],
        )

        to_notify = set()

        for obs in observations:
            msa_users = get_users_in_context(obs, ROLE_MSA, "reminder")
            to_notify.update(msa_users)

        return [
            user for user in to_notify
            if "Manager" not in api.user.get_roles(user=user)
        ]
