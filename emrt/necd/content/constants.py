""" LDAP Role mapping constants.
"""

LDAP_BASE = 'extranet-necd-review'


LDAP_SECRETARIAT = LDAP_BASE + '-secretariat'


LDAP_TERT = LDAP_BASE + '-tert'
LDAP_LEADREVIEW = LDAP_TERT + '-leadreview'
LDAP_SECTOREXP = LDAP_TERT + '-sectorexp'


LDAP_COUNTRIES = LDAP_BASE + '-countries'
LDAP_MSA = LDAP_COUNTRIES + '-msa'
LDAP_MSEXPERT = LDAP_COUNTRIES + '-msexpert'


__all__ = (
    LDAP_BASE,
    LDAP_SECRETARIAT,
    LDAP_TERT,
    LDAP_LEADREVIEW,
    LDAP_SECTOREXP,
    LDAP_COUNTRIES,
    LDAP_MSA,
    LDAP_MSEXPERT,
)
