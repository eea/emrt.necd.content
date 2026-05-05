from AccessControl import getSecurityManager

from Acquisition import aq_inner
from Acquisition import aq_parent
from plone import api
from zExceptions import Unauthorized


READ_ONLY_REVIEWFOLDER_STATES = frozenset(["published"])


def get_parent_reviewfolder(context):
    current = aq_inner(context)
    while current is not None:
        if getattr(current, "portal_type", None) == "ReviewFolder":
            return current
        current = aq_parent(current)
    return None


def reviewfolder_allows_mutation(context):
    reviewfolder = get_parent_reviewfolder(context)
    if reviewfolder is None:
        return True

    sm = getSecurityManager()
    if sm.checkPermission("Manage portal", reviewfolder):
        return True

    return (
        api.content.get_state(reviewfolder)
        not in READ_ONLY_REVIEWFOLDER_STATES
    )


def ensure_reviewfolder_allows_mutation(context):
    if not reviewfolder_allows_mutation(context):
        raise Unauthorized("Review folder is read-only.")
