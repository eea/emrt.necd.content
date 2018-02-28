from zope.component import getUtility
from zope.component.hooks import getSite

import plone.api as api

from emrt.necd.content.utilities.interfaces import ISetupReviewFolderRoles


def run(_):
    portal = getSite()
    getUtility(ISetupReviewFolderRoles)(portal['2018'])


def catalog(_):
    tool = api.portal.get_tool('portal_catalog')
    tool.manage_reindexIndex(ids=('GHG_Source_Category', ))
