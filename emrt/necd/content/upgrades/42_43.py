from Products.CMFCore.utils import getToolByName
import transaction

PROFILE_ID = 'profile-emrt.necd.content:default'


def upgrade(context, logger=None):
    if logger is None:
        from logging import getLogger
        logger = getLogger('emrt.necd.content.upgrades.42_43')

    update_catalog(context, logger)
    catalog_metadata(context, logger)
    logger.info('Upgrade steps executed')


def update_catalog(context, logger):
    setup = getToolByName(context, 'portal_setup')
    setup.runImportStepFromProfile(PROFILE_ID, 'catalog')
    transaction.commit()

def catalog_metadata(context, logger):
    catalog = getToolByName(context, 'portal_catalog')
    logger.info('Reindexing')
    brains = catalog(portal_type='Observation')
    length = len(brains)
    count = 0
    for b in brains:
        count = count + 1
        obj = b.getObject()
        obj.edit()
        logger.info('%s/%s: %s reindexed' % (count, length, obj.getId()))
        if count % 100 == 0:
            transaction.commit()
            logger.info('transaction committed')
