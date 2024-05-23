from logging import getLogger

import transaction
from DateTime import DateTime

from zope.component import getMultiAdapter
from zope.globalrequest import getRequest

from plone.app.textfield.value import RichTextValue

import plone.api as api

import html2text


LOGGER = getLogger(__name__)


def filter_is_carried_over(obs):
    return hasattr(obs, "carryover_from")


def filter_has_comments(obs):
    return (
        getattr(obs, "closing_comments", None)
        or getattr(obs, "closing_deny_comments", None)
    )

def run(_):
    catalog = api.portal.get_tool("portal_catalog")
    brains = catalog(portal_type="Conclusions", modified={"range": "min", "query": DateTime("2024/02/19")})
    brains_len = len(brains)
    a_tenth = brains_len / 10
    conclusions = (brain.getObject() for brain in brains)
    LOGGER.info("Found %s brains. Selecting some...", brains_len)
    valid_conclusions = (
        obj
        for obj in conclusions
        if isinstance(obj.text, RichTextValue)
    )
    for idx, conclusion in enumerate(valid_conclusions, start=1):
        LOGGER.info(conclusion.absolute_url(1))

        try:
            conclusion_html = conclusion.text.output_relative_to(conclusion)
            conclusion.text = html2text.html2text(conclusion_html, bodywidth=0)
        except Exception:
            LOGGER.exception("Could not update conclusion text!")

        conclusion.aq_parent.reindexObject()
        conclusion.reindexObject()

        # log progress
        if a_tenth and idx % a_tenth == 0:
            transaction.savepoint(optimistic=True)
            LOGGER.info("Done %s/%s.", idx, brains_len)
