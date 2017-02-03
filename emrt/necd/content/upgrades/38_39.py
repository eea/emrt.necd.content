from zope.globalrequest import getRequest
from Products.CMFCore.utils import getToolByName

PROFILE_ID = 'profile-emrt.necd.content:default'


def upgrade(context, logger=None):
    if logger is None:
        from logging import getLogger
        logger = getLogger('emrt.necd.content.upgrades.38_39')
    reindex_index(context, logger)
    logger.info('Upgrade steps executed')


def reindex_index(context, logger):
    setup = getToolByName(context, 'portal_setup')
    setup.runImportStepFromProfile(PROFILE_ID, 'catalog')
    logger.info('Reindexing indexes')
    catalog = getToolByName(context, 'portal_catalog')
    catalog.clearFindAndRebuild()

