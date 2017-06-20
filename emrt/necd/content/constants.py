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


ROLE_SE = 'SectorExpert'
ROLE_CP = 'CounterPart'
ROLE_LR = 'LeadReviewer'
ROLE_MSA = 'MSAuthority'
ROLE_MSE = 'MSExpert'


P_OBS_REDRAFT_REASON_VIEW = (
'emrt.necd.content: View Observation Redraft Reason'
)


__all__ = (
    'LDAP_BASE',
    'LDAP_SECRETARIAT',
    'LDAP_TERT',
    'LDAP_LEADREVIEW',
    'LDAP_SECTOREXP',
    'LDAP_COUNTRIES',
    'LDAP_MSA',
    'LDAP_MSEXPERT',
    'ROLE_SE',
    'ROLE_CP',
    'ROLE_LR',
    'ROLE_MSA',
    'ROLE_MSE',
)
