from Products.CMFDiffTool import dexteritydiff
from eea.cache import cache

EXCLUDED_FIELDS = list(dexteritydiff.EXCLUDED_FIELDS)
EXCLUDED_FIELDS.append('ghg_estimations')
dexteritydiff.EXCLUDED_FIELDS = tuple(EXCLUDED_FIELDS)

from logging import getLogger
log = getLogger(__name__)
log.info('Patching difftool excluded fields to add ghg_estimations')


def _cachekey_lookupuserbyattr(meth, self, *args, **kwargs):
    return (meth.__name__, '_'.join(args))


@cache(_cachekey_lookupuserbyattr)
def _lookupuserbyattr_cache_wrapper(result):
    """ Wrapper to raise error when login was not successfull.
        Needed to avoid caching unsuccessfull login attempts.
    """
    if not any(result):
        raise ValueError
    else:
        return result


def _lookupuserbyattr(self, name, value, pwd=None):
    result = self._old__lookupuserbyattr(name, value, pwd)
    try:
        return _lookupuserbyattr_cache_wrapper(result)
    except ValueError:
        return result
    finally:
        return result


def _cachekey_getGroupedUsers(meth, self, groups=None):
    if groups is None:
        groups = self.getGroups()
    return (meth.__name__, self.__name__, groups)


@cache(_cachekey_getGroupedUsers)
def getGroupedUsers(self, groups=None):
    result = self._old_getGroupedUsers(groups)
    return [user.aq_inner.aq_self for user in result]
