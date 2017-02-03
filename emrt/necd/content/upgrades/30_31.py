from Products.CMFCore.utils import getToolByName
from emrt.necd.content.roles.localrolesubscriber import grant_local_roles

PROFILE_ID = 'profile-emrt.necd.content:default'


def upgrade(context, logger=None):
    if logger is None:
        from logging import getLogger
        logger = getLogger('emrt.necd.content.upgrades.30_31')

    install_sharing(context, logger)
    reassign_localroles(context, logger)
    logger.info('Upgrade steps executed')


def install_sharing(context, logger):
    setup = getToolByName(context, 'portal_setup')
    setup.runImportStepFromProfile(PROFILE_ID, 'sharing')
    logger.info('Security settings updated')


def reassign_localroles(context, logger):
    catalog = getToolByName(context, 'portal_catalog')
    for brain in catalog.unrestrictedSearchResults(portal_type='Observation'):
        observation = brain.getObject()
        grant_local_roles(observation)
        logger.info('Granted to %s' % brain.getPath())

    logger.info('Local roles granted')
