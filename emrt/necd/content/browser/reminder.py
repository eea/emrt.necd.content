import os
from operator import attrgetter
from collections import namedtuple
from collections import defaultdict

from zope.component import getMultiAdapter
from zope.component import getUtility

from zope.schema.interfaces import IVocabularyFactory

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



UserData = namedtuple(
    "UserData",
    ["user_id", "name", "email", "roles", "country_a2", "country_name"]
)

CountryData = namedtuple(
    "CountryData",
    ["a2", "name", "user_count"]
)

class ReminderView(BrowserView):

    known_parameters = (
        ("username", "The receiving user's name.", ),
        ("tool_url", "The absolute URL of this review folder.", ),
    )

    @property
    def mail_from_address(self):
        return api.portal.get().email_from_address

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
        v_ms = getUtility(
            IVocabularyFactory,
            name='emrt.necd.content.eea_member_states')(self.context)

        if "Manager" in api.user.get_roles():
            result = []
            for user, country_a2 in self._get_users_to_notify():
                roles = api.user.get_roles(user=user, obj=self.context)
                user_data = (
                    user.getId(),
                    safer_unicode(user.getProperty("fullname", user.getId())),
                    user.getProperty("email", "-"),
                    [r for r in roles if r != "Authenticated"],
                    country_a2,
                    v_ms.getTerm(country_a2).title
                )
                result.append(UserData(*user_data))
            return sorted(result, key=attrgetter("name"))


    @property
    def countries_to_notify(self):
        v_ms = getUtility(
            IVocabularyFactory,
            name='emrt.necd.content.eea_member_states')(self.context)

        result = defaultdict(set)
        for user, country_a2 in self._get_users_to_notify():
            result[country_a2].add(user.getId())

        return sorted(
            [
                CountryData(a2, v_ms.getTerm(a2).title, len(users))
                for a2, users
                in result.items()
            ],
            key=attrgetter("name")
        )


    def send_reminder(self):
        subject = self.request.get("subject", self.default_subject)
        content = self.request.get("content", self.default_content)
        countries_a2 = self.request.get("countries_a2", [])
        user_ids = (
            self.request.get("user_ids", [])
            if "Manager" in api.user.get_roles()
            else []
        )

        template = PageTextTemplate(content)

        if user_ids:
            to_notify = [
                user for user, _ in self._get_users_to_notify()
                if user.getId() in user_ids
            ]
        else:
            to_notify = [
                user for user, a2 in self._get_users_to_notify()
                if a2 in countries_a2
            ]

        for user in to_notify:
            self._send_email(subject, template, user)

        if to_notify:
            portal_message = "Notified {} users.".format(len(to_notify))
        else:
            portal_message = "Nothing selected, nobody was notified."
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
            msa_users = [
                (user, obs.country)
                for user
                in get_users_in_context(obs, ROLE_MSA, "reminder")
            ]
            to_notify.update(msa_users)

        return [
            (user, a2) for user, a2 in to_notify
            if "Manager" not in api.user.get_roles(user=user)
        ]