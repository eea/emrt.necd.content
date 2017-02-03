from Products.CMFCore.utils import getToolByName


PROFILE_ID = 'profile-emrt.necd.content:default'


def upgrade(context, logger=None):
    if logger is None:
        from logging import getLogger
        logger = getLogger('emrt.necd.content.upgrades.2_3')

    install_workflow(context, logger)
    logger.info('Upgrade steps executed')


def install_workflow(context, logger):
    setup = getToolByName(context, 'portal_setup')
    setup.runImportStepFromProfile(PROFILE_ID, 'rolemap')
    setup.runImportStepFromProfile(PROFILE_ID, 'workflow')
    setup.runImportStepFromProfile(PROFILE_ID, 'sharing')
    setup.runImportStepFromProfile(PROFILE_ID, 'typeinfo')
    logger.info('Resinstalled  Workflows')
