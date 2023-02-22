from logging import getLogger

import plone.api as api
from Products.CMFCore.utils import getToolByName


LOGGER = getLogger(__name__)


def delete_voc(portal):
    atvm = getToolByName(portal, "portal_vocabularies")
    atvm._delObject("highlight")


def run(_):
    portal = api.portal.get()
    delete_voc(portal)
