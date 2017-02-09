""" LDAP Role mapping constants.
"""

LDAP_BASE = 'extranet-necd-review'


LDAP_TERT = LDAP_BASE + '-tert'
LDAP_LEADREVIEW = LDAP_TERT + '-leadreview'
LDAP_SECTOREXP = LDAP_TERT +'-sectorexp'


LDAP_COUNTRIES = LDAP_BASE + '-countries'
LDAP_MSA = LDAP_COUNTRIES + '-msa'
LDAP_MSEXPERT = LDAP_COUNTRIES + '-msexpert'


__all__ = (
    LDAP_BASE.__name__,
    LDAP_TERT.__name__,
    LDAP_LEADREVIEW.__name__,
    LDAP_SECTOREXP.__name__,
    LDAP_COUNTRIES.__name__,
    LDAP_MSA.__name__,
    LDAP_MSEXPERT.__name__,
)