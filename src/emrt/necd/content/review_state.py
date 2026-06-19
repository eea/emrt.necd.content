import datetime
import re

from AccessControl import getSecurityManager

from Acquisition import aq_inner
from Acquisition import aq_parent
from plone import api
from zExceptions import Unauthorized


READ_ONLY_REVIEWFOLDER_STATES = frozenset(["published"])
REVIEW_CYCLE_YEAR_RE = re.compile(r"(?<!\d)(\d{4})(?!\d)")


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


def _extract_year(value):
    if not value:
        return None

    match = REVIEW_CYCLE_YEAR_RE.search(str(value))
    if match:
        return int(match.group(1))

    return None


def _title(context):
    try:
        return context.Title()
    except AttributeError:
        return getattr(context, "title", "")


def get_review_cycle_year(context):
    """Return the review cycle year for an observation-like context."""
    reviewfolder = get_parent_reviewfolder(context)
    if reviewfolder is not None:
        year = _extract_year(reviewfolder.getId())
        if year is not None:
            return year

        year = _extract_year(_title(reviewfolder))
        if year is not None:
            return year

    year = _extract_year(getattr(context, "review_year", None))
    if year is not None:
        return year

    return datetime.datetime.now().year
