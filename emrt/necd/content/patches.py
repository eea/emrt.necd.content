"""Patches."""

import hashlib
from logging import getLogger
from typing import List

from Products.CMFDiffTool import dexteritydiff

from plone.memoize.ram import cache

EXCLUDED_FIELDS: List[str] = list(dexteritydiff.EXCLUDED_FIELDS)
EXCLUDED_FIELDS.append("ghg_estimations")
dexteritydiff.EXCLUDED_FIELDS = tuple(EXCLUDED_FIELDS)

log = getLogger(__name__)
log.info("Patching difftool excluded fields to add ghg_estimations")


def _sha_cachekey(sig):
    return hashlib.sha256(str(sig).encode()).hexdigest()


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


def _cachekey(meth, self, *args, **kwargs):
    kw = tuple([(k, v) for k, v in kwargs.items()])
    sig = (meth.__name__, self.__name__, args, kw)
    return _sha_cachekey(sig)


@cache(_cachekey)
def cache_wrapper(meth, *args, **kwargs):
    """Wrapper."""
    return meth(*args, **kwargs)


def LDAPPrincipals_search(self, *args, **kwargs):
    """Patch LDAPPrincipals.search."""
    return cache_wrapper(self._old_search, *args, **kwargs)
