from Products.CMFCore.utils import getToolByName


PROFILE_ID = 'profile-emrt.necd.content:default'


def upgrade(context, logger=None):
    if logger is None:
        from logging import getLogger
        logger = getLogger('emrt.necd.content.upgrades.4_5')

    install_workflow(context, logger)
    logger.info('Upgrade steps executed')


def install_workflow(context, logger):
    setup = getToolByName(context, 'portal_setup')
    wtool = getToolByName(context, 'portal_workflow')
    wtool.manage_delObjects(['esd-question-review-workflow'])
    setup.runImportStepFromProfile(PROFILE_ID, 'workflow')
    logger.info('Reinstalled  Workflows')
