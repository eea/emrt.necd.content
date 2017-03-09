import logging
from functools import partial
import concurrent.futures
from Products.Five.browser import BrowserView
from emrt.necd.content import constants
import plone.api as api

LOGGER = logging.getLogger(__name__)

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
    'is',
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


def append_string(sep, base, tail):
    return '{}{}{}'.format(base, sep, tail)


APPEND_MINUS = partial(append_string, '-')
APPEND_EMPTY = partial(append_string, '')


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


def concurrent_loop(workers, timeout, func, items, *args):
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(func, item, *args) for item in items]
        LOGGER.info("Executing total %s jobs on %s workers", len(futures), workers)
        for idx, future in enumerate(concurrent.futures.as_completed(futures, timeout=timeout)):
            results.append(future.result())
            LOGGER.info("Processed job %s", idx)
    return results


CONCURRENT = partial(concurrent_loop, 32, 600.0)


class Warmup(BrowserView):
    def __call__(self):
        portal_groups = api.portal.get_tool('portal_groups')
        plone_groups = CONCURRENT(portal_groups.getGroupById, GROUPS)
        for group in plone_groups:
            group.getGroupMembers()
        return plone_groups
