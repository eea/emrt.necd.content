from Products.CMFDiffTool import dexteritydiff

EXCLUDED_FIELDS = list(dexteritydiff.EXCLUDED_FIELDS)
EXCLUDED_FIELDS.append('ghg_estimations')
dexteritydiff.EXCLUDED_FIELDS = tuple(EXCLUDED_FIELDS)

from logging import getLogger
log = getLogger(__name__)
log.info('Patching difftool excluded fields to add ghg_estimations')
