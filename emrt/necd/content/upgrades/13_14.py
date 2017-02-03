from Products.CMFCore.utils import getToolByName
from emrt.necd.content.setuphandlers import prepareVocabularies

PROFILE_ID = 'profile-emrt.necd.content:default'


def upgrade(context, logger=None):
    if logger is None:
        from logging import getLogger
        logger = getLogger('emrt.necd.content.upgrades.13_14')

    #install_workflow(context, logger)
    css_and_js(context, logger)
    reimport_vocabularies(context, logger)
    logger.info('Upgrade steps executed')


def reimport_vocabularies(context, logger):
    atvm = getToolByName(context, 'portal_vocabularies')
    del atvm['highlight']
    psetup = getToolByName(context, 'portal_setup')
    profile = psetup._getImportContext(PROFILE_ID)
    prepareVocabularies(context, profile)


def css_and_js(context, logger):
    setup = getToolByName(context, 'portal_setup')
    setup.runImportStepFromProfile(PROFILE_ID, 'cssregistry')
    setup.runImportStepFromProfile(PROFILE_ID, 'jsregistry')
    logger.info('Reload CSS and JS')


def install_workflow(context, logger):
    setup = getToolByName(context, 'portal_setup')
    wtool = getToolByName(context, 'portal_workflow')
    wtool.manage_delObjects([
        'esd-question-review-workflow',
        'esd-review-workflow',
        'esd-answer-workflow',
        'esd-comment-workflow',
        'esd-file-workflow',
        ])
    setup.runImportStepFromProfile(PROFILE_ID, 'rolemap')
    setup.runImportStepFromProfile(PROFILE_ID, 'workflow')
    setup.runImportStepFromProfile(PROFILE_ID, 'sharing')
    setup.runImportStepFromProfile(PROFILE_ID, 'typeinfo')
    logger.info('Reinstalled  Workflows')
    wtool.updateRoleMappings()
    logger.info('Security settings updated')
