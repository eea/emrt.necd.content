import plone.api as api
from Products.CMFCore.utils import getToolByName


def delete_voc(portal):
    atvm = getToolByName(portal, 'portal_vocabularies')
    atvm._delObject('highlight_projection')


def run(_):
    portal = api.portal.get()
    delete_voc(portal)
