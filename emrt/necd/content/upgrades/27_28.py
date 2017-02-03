from Products.CMFCore.utils import getToolByName
from emrt.necd.content.setuphandlers import prepareVocabularies


PROFILE_ID = 'profile-emrt.necd.content:default'


def upgrade(context, logger=None):
    if logger is None:
        from logging import getLogger
        logger = getLogger('emrt.necd.content.upgrades.27_28')

    reimport_vocabularies(context, logger)
    logger.info('Upgrade steps executed')


def reimport_vocabularies(context, logger):
    atvm = getToolByName(context, 'portal_vocabularies')
    del atvm['crf_code']
    psetup = getToolByName(context, 'portal_setup')
    profile = psetup._getImportContext(PROFILE_ID)
    prepareVocabularies(context, profile)
