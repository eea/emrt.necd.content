from time import time
import itertools
from functools import partial
from Products.Five.browser import BrowserView
from emrt.necd.content import constants
from emrt.necd.content import utils
import plone.api as api


COUNTRIES = (
    'at',
    'be',
    'bg',
    'cy',
    'cz',
    'de',
    'dk',
    'ee',
    'es',
    'fi',
    'fr',
    'gb',
    'gr',
    'hu',
    'ie',
    'hr',
    'it',
    'lt',
    'lu',
    'lv',
    'mt',
    'nl',
    'pl',
    'pt',
    'ro',
    'se',
    'si',
    'sk',
)


APPEND_MINUS = partial(utils.append_string, '-')
APPEND_EMPTY = partial(utils.append_string, '')


def partial_for_base(base):
    return partial(APPEND_MINUS, base)


GENERATE_MSA = partial(APPEND_MINUS, constants.LDAP_MSA)
GENERATE_MSEXPERT = partial(APPEND_MINUS, constants.LDAP_MSEXPERT)
GENERATE_LEADREVIEW = partial(APPEND_MINUS, constants.LDAP_LEADREVIEW)

SECTOR_BASE = '{}-sector'.format(constants.LDAP_SECTOREXP)
GENERATE_SECTOR = partial(APPEND_EMPTY, SECTOR_BASE)

SECTORS = tuple(map(GENERATE_SECTOR, range(1, 10)))

COUNTRIES_MSA = tuple(map(GENERATE_MSA, COUNTRIES))
COUNTRIES_MSEXPERT = tuple(map(GENERATE_MSEXPERT, COUNTRIES))
COUNTRIES_LEADREVIEW = tuple(map(GENERATE_LEADREVIEW, COUNTRIES))

SECTOR_PARTIALS = tuple(map(partial_for_base, SECTORS))
COUNTRIES_SECTORS = tuple([p(c) for p in SECTOR_PARTIALS for c in COUNTRIES])


BASE_GROUPS = (
    constants.LDAP_BASE,
    constants.LDAP_COUNTRIES,
    constants.LDAP_MSA,
    constants.LDAP_MSEXPERT,
    constants.LDAP_SECRETARIAT,
    constants.LDAP_TERT,
    constants.LDAP_LEADREVIEW,
    constants.LDAP_SECTOREXP,
)

GROUPS = (
    BASE_GROUPS +
    COUNTRIES_MSA +
    COUNTRIES_MSEXPERT +
    COUNTRIES_LEADREVIEW +
    SECTORS +
    COUNTRIES_SECTORS
)


CONCURRENT = partial(utils.concurrent_loop, 16, 600.0)


def _get_group_members(group):
    try:
        return group.getGroupMembers()
    except (TypeError, AttributeError):
        return tuple()


def _get_group(portal_groups, groupname):
    try:
        return portal_groups.getGroupById(groupname)
    except AttributeError:
        return None


class Warmup(BrowserView):
    def __call__(self):
        start_at = time()
        portal_groups = api.portal.get_tool('portal_groups')
        get_group = partial(_get_group, portal_groups)
        plone_groups = CONCURRENT(get_group, GROUPS)
        members = CONCURRENT(_get_group_members, plone_groups)

        msg = 'OK. {} groups. {} unique members. Duration {} seconds.'.format(
            len(plone_groups),
            len(tuple(set(itertools.chain(*members)))),
            time() - start_at
        )

        return msg
