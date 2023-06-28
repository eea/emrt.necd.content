"""Patches."""

from logging import getLogger
from typing import List

from Products.CMFDiffTool import dexteritydiff

EXCLUDED_FIELDS: List[str] = list(dexteritydiff.EXCLUDED_FIELDS)
EXCLUDED_FIELDS.append("ghg_estimations")
dexteritydiff.EXCLUDED_FIELDS = tuple(EXCLUDED_FIELDS)

log = getLogger(__name__)
log.info("Patching difftool excluded fields to add ghg_estimations")


@property
def Group_existing_member_ids(self):
    """Patched Group.existing_member_ids."""
    return self.translate_ids(
        self.context.attrs.get(self._member_attribute, list())
    )


def LDAPUserPropertySheet__init__(self, principal, plugin):
    """Patched LDAPUserPropertySheet.__init__.
    
    Join fullname if it's a list.
    """
    self._old___init__(principal, plugin)
    fullname = self._properties.get("fullname", "")
    if isinstance(fullname, (list, tuple)):
        self._properties["fullname"] = " ".join(fullname)