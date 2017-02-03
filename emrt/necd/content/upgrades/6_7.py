from Products.CMFCore.utils import getToolByName

PROFILE_ID = 'profile-emrt.necd.content:default'


def upgrade(context, logger=None):
    if logger is None:
        from logging import getLogger
        logger = getLogger('emrt.necd.content.upgrades.6_7')

    content_types(context, logger)
    install_workflow(context, logger)
    logger.info('Upgrade steps executed')


def content_types(context, logger):
    setup = getToolByName(context, 'portal_setup')
    setup.runImportStepFromProfile(PROFILE_ID, 'typeinfo')
    setup.runImportStepFromProfile(PROFILE_ID, 'rolemap')
    setup.runImportStepFromProfile(PROFILE_ID, 'difftool')
    logger.info('Content-types reinstalled')


def install_workflow(context, logger):
    setup = getToolByName(context, 'portal_setup')
    wtool = getToolByName(context, 'portal_workflow')
    wtool.manage_delObjects([
        'esd-question-review-workflow',
        'esd-review-workflow',
        'esd-answer-workflow',
        'esd-comment-workflow',
        ])
    setup.runImportStepFromProfile(PROFILE_ID, 'workflow')
    logger.info('Reinstalled  Workflows')
    wtool.updateRoleMappings()
    logger.info('Security settings updated')
