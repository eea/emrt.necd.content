from five import grok
from plone import api
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary

from emrt.necd.content.constants import LDAP_SECTOREXP


class MSVocabulary(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        pvoc = api.portal.get_tool('portal_vocabularies')
        voc = pvoc.getVocabularyByName('eea_member_states')
        terms = []
        if voc is not None:
            for key, value in voc.getVocabularyLines():
                # create a term - the arguments are the value, the token, and
                # the title (optional)
                terms.append(SimpleVocabulary.createTerm(key, key, value))
        return SimpleVocabulary(terms)

grok.global_utility(MSVocabulary, name=u"emrt.necd.content.eea_member_states")


class GHGSourceCategory(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        pvoc = api.portal.get_tool('portal_vocabularies')
        voc = pvoc.getVocabularyByName('ghg_source_category')
        terms = []
        if voc is not None:
            for key, value in voc.getVocabularyLines():
                # create a term - the arguments are the value, the token, and
                # the title (optional)
                terms.append(SimpleVocabulary.createTerm(key, key, value))
        return SimpleVocabulary(terms)

grok.global_utility(GHGSourceCategory,
    name=u"emrt.necd.content.ghg_source_category")


class GHGSourceSectors(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        pvoc = api.portal.get_tool('portal_vocabularies')
        voc = pvoc.getVocabularyByName('ghg_source_sectors')
        terms = []
        if voc is not None:
            for key, value in voc.getVocabularyLines():
                # create a term - the arguments are the value, the token, and
                # the title (optional)
                terms.append(SimpleVocabulary.createTerm(key, key, value))
        return SimpleVocabulary(terms)

grok.global_utility(GHGSourceSectors,
    name=u"emrt.necd.content.ghg_source_sectors")


class Pollutants(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        pvoc = api.portal.get_tool('portal_vocabularies')
        voc = pvoc.getVocabularyByName('pollutants')
        terms = []
        if voc is not None:
            for key, value in voc.getVocabularyLines():
                # create a term - the arguments are the value, the token, and
                # the title (optional)
                terms.append(SimpleVocabulary.createTerm(key, key, value))
        return SimpleVocabulary(terms)

grok.global_utility(Pollutants,
    name=u"emrt.necd.content.pollutants")


class Fuel(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        pvoc = api.portal.get_tool('portal_vocabularies')
        voc = pvoc.getVocabularyByName('fuel')
        terms = []
        if voc is not None:
            for key, value in voc.getVocabularyLines():
                # create a term - the arguments are the value, the token, and
                # the title (optional)
                terms.append(SimpleVocabulary.createTerm(key, key, value))
        return SimpleVocabulary(terms)

grok.global_utility(Fuel,
    name=u"emrt.necd.content.fuel")


class Highlight(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        pvoc = api.portal.get_tool('portal_vocabularies')
        voc = pvoc.getVocabularyByName('highlight')
        terms = []
        if voc is not None:
            for key, value in voc.getVocabularyLines():
                # create a term - the arguments are the value, the token, and
                # the title (optional)
                terms.append(SimpleVocabulary.createTerm(key, key, value))
        return SimpleVocabulary(terms)

grok.global_utility(Highlight,
    name=u"emrt.necd.content.highlight")


class Parameter(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        pvoc = api.portal.get_tool('portal_vocabularies')
        voc = pvoc.getVocabularyByName('parameter')
        terms = []
        if voc is not None:
            for key, value in voc.getVocabularyLines():
                # create a term - the arguments are the value, the token, and
                # the title (optional)
                terms.append(SimpleVocabulary.createTerm(key, key, value))
        return SimpleVocabulary(terms)

grok.global_utility(Parameter,
    name=u"emrt.necd.content.parameter")


class StatusFlag(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        pvoc = api.portal.get_tool('portal_vocabularies')
        voc = pvoc.getVocabularyByName('status_flag')
        terms = []
        if voc is not None:
            for key, value in voc.getVocabularyLines():
                # create a term - the arguments are the value, the token, and
                # the title (optional)
                terms.append(SimpleVocabulary.createTerm(key, key, value))
        return SimpleVocabulary(terms)

grok.global_utility(StatusFlag,
    name=u"emrt.necd.content.status_flag")


from .nfr_code_matching import nfr_codes

class NFRCode(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        terms = []
        nfrcodes = nfr_codes()

        try:
            user = api.user.get_current()
        except Exception:
            user = None

        have_user = user is not None and not api.user.is_anonymous()
        if have_user:
            user_groups = user.getGroups()

        for key, value in nfrcodes.items():
            # if there's an active user, show only NFR codes
            # part of the user's ldap sector
            valid = False
            if have_user:
                for group in user_groups:
                    if valid:
                        break

                    valid_prefix = '{}-{}-'.format(
                        LDAP_SECTOREXP,
                        value['ldap']
                    )

                    valid = group.startswith(valid_prefix)
                if not valid:
                    # skip this term
                    continue

            # create a term - the arguments are the value, the token, and
            # the title (optional)
            term = SimpleVocabulary.createTerm(key, key, value['title'])
            terms.append(term)

        return SimpleVocabulary(terms)

grok.global_utility(NFRCode, name=u"emrt.necd.content.nfr_code")


class Conclusions(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        pvoc = api.portal.get_tool('portal_vocabularies')
        voc = pvoc.getVocabularyByName('conclusion_reasons')
        terms = []
        if voc is not None:
            for key, value in voc.getVocabularyLines():
                # create a term - the arguments are the value, the token, and
                # the title (optional)
                terms.append(SimpleVocabulary.createTerm(key, key, value))
        return SimpleVocabulary(terms)

grok.global_utility(Conclusions, name=u"emrt.necd.content.conclusion_reasons")
