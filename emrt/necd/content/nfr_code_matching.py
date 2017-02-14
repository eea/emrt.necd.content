from zope.interface import Interface
from zope import schema
from zope.component import getUtility
from plone.registry.interfaces import IRegistry
from emrt.necd.content import MessageFactory as _
from logging import getLogger
from collections import OrderedDict
logger = getLogger('emrt.necd.content.nfr_codes')


class INECDSettings(Interface):
    """Settings expected to be found in plone.registry
    """

    nfrcodeMapping = schema.Dict(
        title=_(u"NFR Codes"),
        description=_(u"Maps ldap sectors"),
        key_type=schema.TextLine(title=_(u"Code")),
        value_type=schema.TextLine(
            title=_(u"Sector Item"),
            description=_(u"Descripe a sector in the form: ldap|code|name|title")
        ),
    )


def nfr_codes():
    """ get the NFR code mapping from portal_registry
        @retrun a dictionary
        {
            "key": {
                "ldap": "sector",
                "code": "key",
                "name": "name",
                "title": "title"
            },
            ...
        }
    """
    registry = getUtility(IRegistry)
    nfrcodeMapping = registry.forInterface(INECDSettings).nfrcodeMapping

    nfr_codes = {}

    for key, codes in nfrcodeMapping.items():
        try:
            ldap, code, name, title = codes.split('|')
            nfr_codes[key] = {
                "ldap": ldap,
                "code": code,
                "name": name,
                "title": title
            }
        except:
            logger.warning('%s is not well formatted' % key)

    return OrderedDict(sorted(nfr_codes.items()))


def get_category_ldap_from_nfr_code(value):
    """ get the NFR category this NFR Code matches
        According to the rules previously set
        for LDAP Matching
    """
    nfrcodes = nfr_codes()
    return nfrcodes.get(value, {}).get('ldap', '')


def get_category_value_from_nfr_code(value):
    """ get the NFR category value to show it in the observation metadata """
    nfrcodes = nfr_codes()
    # return nfr_codes.get(value, {}).get('sectorname', '')
    return nfrcodes.get(value, {}).get('title', '')
