from functools import partial
from itertools import chain
from itertools import product
from itertools import ifilter as filter

from zope.component.hooks import getSite
from zope.component import getUtility

from emrt.necd.content.utilities.interfaces import ILDAPQuery

from emrt.necd.content.utilities import ldap_utils

from emrt.necd.content.constants import LDAP_SECTOREXP
from emrt.necd.content.constants import LDAP_LEADREVIEW
from emrt.necd.content.constants import LDAP_MSA
from emrt.necd.content.constants import ROLE_MSA
from emrt.necd.content.constants import ROLE_SE
from emrt.necd.content.constants import ROLE_LR


QUERY_LDAP_ROLES = ldap_utils.format_or(
    'cn', (
        LDAP_MSA + '-*',
        LDAP_LEADREVIEW + '-*',
        LDAP_SECTOREXP + '-sector*-*'
    )
)


def f_start(pat, s):
    return s.startswith(pat)


f_start_msa = partial(f_start, LDAP_MSA)
f_start_lr = partial(f_start, LDAP_LEADREVIEW)
f_start_se = partial(f_start, LDAP_SECTOREXP)


def setup_reviewfolder_roles(folder):
    site = getSite()
    acl = site['acl_users']['ldap-plugin']['acl_users']

    with getUtility(ILDAPQuery)(acl, paged=True) as q_ldap:
        q_groups = q_ldap.query_groups(QUERY_LDAP_ROLES, ('cn',))


    groups = [r[1]['cn'][0] for r in q_groups]

    grant = chain(
        product([ROLE_MSA], filter(f_start_msa, groups)),
        product([ROLE_LR], filter(f_start_lr, groups)),
        product([ROLE_SE], filter(f_start_se, groups)),
    )

    for role, g_name in grant:
        folder.manage_setLocalRoles(g_name, [role])

    return folder


class SetupReviewFolderRoles(object):
    def __call__(self, folder):
        return setup_reviewfolder_roles(folder)
