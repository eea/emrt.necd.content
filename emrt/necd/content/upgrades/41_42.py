from Products.CMFCore.utils import getToolByName
from emrt.necd.content.roles.localrolesubscriber import grant_local_roles
import transaction

PROFILE_ID = 'profile-emrt.necd.content:default'


def upgrade(context, logger=None):
    if logger is None:
        from logging import getLogger
        logger = getLogger('emrt.necd.content.upgrades.41_42')

    reassign_localroles(context, logger)
    logger.info('Upgrade steps executed')


def reassign_localroles(context, logger):
    catalog = getToolByName(context, 'portal_catalog')
    count = 0
    brains = catalog.unrestrictedSearchResults(portal_type='Observation')
    length = len(brains)
    for brain in brains:
        count = count + 1
        observation = brain.getObject()
        grant_local_roles(observation)
        logger.info('%s/%s: Granted to %s' % (count, length, brain.getPath()))
        if count % 100 == 0:
            transaction.commit()

    logger.info('Local roles granted')
