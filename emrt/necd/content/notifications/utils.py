from typing import List
from typing import cast

from cs.htmlmailer.mailer import create_html_mail

from Acquisition import aq_inner
from Acquisition import aq_parent
from zope.globalrequest import getRequest

from Products.CMFCore.MemberDataTool import MemberAdapter
from Products.CMFPlone.PloneTool import PloneTool

from plone import api
from plone.base.utils import safe_text

from emrt.necd.content.constants import VALID_ROLES
from emrt.necd.content.reviewfolder import IReviewFolder
from emrt.necd.content.subscriptions.interfaces import (
    INotificationUnsubscriptions,
)


def notify(
    observation, template, subject, role: VALID_ROLES, notification_name
):
    users = get_users_in_context(observation, role, notification_name)
    content = template(**dict(observation=observation))

    if observation.aq_parent.type == "projection":
        prepend = "[NECD Projection Review]"
    else:
        prepend = "[NECD Inventory Review]"

    subject = "{} {}".format(prepend, subject)

    send_mail(subject, safe_text(content), users)


def send_mail(subject, email_content, users=[]):
    """Effectively send the e-mail message."""
    from logging import getLogger

    log = getLogger(__name__)

    user_emails = extract_emails(users)
    if user_emails:
        to_addr = user_emails[0]
        cc_addrs = user_emails[1:]
        getRequest()

        mail = create_html_mail(
            subject,
            html=email_content,
            cc_addrs=cc_addrs,
        )

        try:
            api.portal.send_email(
                recipient=to_addr, subject=subject, body=mail
            )
            message = "Users have been notified by e-mail"
            log.info(
                "Emails sent to users %s",
                ", ".join(
                    [email.replace("@", " <at> ") for email in user_emails]
                ),
            )
            api.portal.show_message(message)
        except Exception as e:
            message = "There was an error sending the notification, but your action was completed succesfuly. Contact the EEA Secretariat for further instructions."
            log.error("Error when sending the notification: %s", e)
            api.portal.show_message(message, type="error")


def extract_emails(users: List[MemberAdapter]):
    """Get the email of each user."""
    putils: PloneTool = api.portal.get_tool(name="plone_utils")
    emails: List[str] = []
    for user in users:
        email: str = cast(str, user.getProperty("email"))
        if email and putils.validateSingleEmailAddress(email):
            emails.append(email)

    return list(set(emails))


def get_users_in_context(observation, role, notification_name):
    users = []
    local_roles = observation.get_local_roles()

    usernames = []
    for username, userroles in local_roles:
        if role in userroles:
            group = api.group.get(username)
            if group:
                usernames.extend(group.getMemberIds())
            else:
                usernames.append(username)

    usernames = list(set(usernames))

    for username in usernames:
        user = api.user.get(username=username)
        if user is not None:
            if not exclude_user_from_notification(
                observation, user, role, notification_name
            ):
                users.append(user)
        else:
            from logging import getLogger

            log = getLogger(__name__)
            log.info("Username %s has no user object", username)

    return users


def exclude_user_from_notification(observation, user, role, notification):
    adapted = INotificationUnsubscriptions(observation)
    data = adapted.get_user_data(user.getId())
    if not data:
        area = aq_parent(aq_inner(observation))
        if IReviewFolder.providedBy(area):
            adapted = INotificationUnsubscriptions(area)
            data = adapted.get_user_data(user.getId())
    excluded_notifications = data.get(role, [])
    return notification in excluded_notifications
