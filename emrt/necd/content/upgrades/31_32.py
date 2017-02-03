from Products.CMFCore.utils import getToolByName

PROFILE_ID = 'profile-emrt.necd.content:default'


def upgrade(context, logger=None):
    if logger is None:
        from logging import getLogger
        logger = getLogger('emrt.necd.content.upgrades.31_32')

    install_catalog(context, logger)
    logger.info('Upgrade steps executed')


def install_catalog(context, logger):
    setup = getToolByName(context, 'portal_setup')
    setup.runImportStepFromProfile(PROFILE_ID, 'catalog')
    logger.info('Catalog updated. Reindexing.')
    catalog = getToolByName(context, 'portal_catalog')
    catalog.clearFindAndRebuild()
    logger.info('Reindexed')
