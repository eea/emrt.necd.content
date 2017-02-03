from Products.CMFCore.utils import getToolByName


PROFILE_ID = 'profile-emrt.necd.content:default'


def upgrade(context, logger=None):
    if logger is None:
        from logging import getLogger
        logger = getLogger('emrt.necd.content.upgrades.16_17')

    install_workflow(context, logger)
    logger.info('Upgrade steps executed')


def install_workflow(context, logger):
    setup = getToolByName(context, 'portal_setup')
    wtool = getToolByName(context, 'portal_workflow')
    wtool.manage_delObjects([
        'esd-answer-workflow',
        'esd-comment-workflow',
        'esd-conclusion-workflow',
        'esd-file-workflow',
        'esd-question-review-workflow',
        'esd-reviewtool-folder-workflow',
        'esd-review-workflow',
        ])
    setup.runImportStepFromProfile(PROFILE_ID, 'rolemap')
    setup.runImportStepFromProfile(PROFILE_ID, 'workflow')
    setup.runImportStepFromProfile(PROFILE_ID, 'sharing')
    setup.runImportStepFromProfile(PROFILE_ID, 'typeinfo')
    logger.info('Reinstalled  Workflows')
    wtool.updateRoleMappings()
    logger.info('Security settings updated')
