from zope.component import getUtility
from zope.component.hooks import getSite

from emrt.necd.content.utilities.interfaces import ISetupReviewFolderRoles


def run(_):
    portal = getSite()
    getUtility(ISetupReviewFolderRoles)(portal['2018'])
