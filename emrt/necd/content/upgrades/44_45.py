from zope.globalrequest import getRequest
from Products.CMFCore.utils import getToolByName
from emrt.necd.content.setuphandlers import prepareVocabularies

PROFILE_ID = 'profile-emrt.necd.content:default'


def upgrade(context, logger=None):
    if logger is None:
        from logging import getLogger
        logger = getLogger('emrt.necd.content.upgrades.44_45')

    install_workflow(context, logger)
    logger.info('Upgrade steps executed')

def install_workflow(context, logger):
    setup = getToolByName(context, 'portal_setup')
    wtool = getToolByName(context, 'portal_workflow')
    setup.runImportStepFromProfile(PROFILE_ID, 'workflow')
    logger.info('Reinstalled Workflows')
    wtool.updateRoleMappings()
    logger.info('Security settings updated')
