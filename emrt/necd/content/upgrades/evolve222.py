import plone.api as api
from Products.CMFCore.utils import getToolByName

def run(_):
    portal = api.portal.get()

    atvm = getToolByName(portal, 'portal_vocabularies')
    atvm._delObject('parameter')