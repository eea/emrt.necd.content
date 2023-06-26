"""Patches."""

import hashlib
from logging import getLogger

from Products.CMFDiffTool import dexteritydiff

from plone.memoize.ram import cache

EXCLUDED_FIELDS = list(dexteritydiff.EXCLUDED_FIELDS)
EXCLUDED_FIELDS.append("ghg_estimations")
dexteritydiff.EXCLUDED_FIELDS = tuple(EXCLUDED_FIELDS)

log = getLogger(__name__)
log.info("Patching difftool excluded fields to add ghg_estimations")


def _sha_cachekey(sig):
    return hashlib.sha256(str(sig).encode()).hexdigest()


def _cachekey_LDAPSession_search(meth, self, *args, **kwargs):
    kw = tuple([(k, v) for k, v in kwargs.items()])
    sig = (meth.__name__, self.__name__, args, kw)
    return _sha_cachekey(sig)


@cache(_cachekey_LDAPSession_search)
def LDAPSession_search_cache_wrapper(meth, *args, **kwargs):
    """Wrapper."""
    result = meth(*args, **kwargs)
    return result


def LDAPSession_search(self, *args, **kwargs):
    """Patch LDAPSession.search."""
    try:
        return LDAPSession_search_cache_wrapper(self._old_search, *args, **kwargs)
    except ValueError as exc:
        return exc.message
