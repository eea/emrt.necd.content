from five import grok
from plone import api
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary

from emrt.necd.content.constants import LDAP_SECTOREXP


def mk_term(key, value):
    return SimpleVocabulary.createTerm(key, key, value)


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
        if voc is None:
            return SimpleVocabulary([])

        terms = [mk_term(*pair) for pair in voc.getVocabularyLines()]
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

        def get_valid_user():
            try:
                user = api.user.get_current()
            except Exception:
                return None

            return user if user and not api.user.is_anonymous() else None

        def validate_term(prefix, groups):
            return tuple([
                group for group in groups
                if group.startswith(prefix)
            ])

        def build_prefix(ldap_role, sector):
            return '{}-{}-'.format(ldap_role, sector)

        def vocab_from_terms(*terms):
            return SimpleVocabulary([
                SimpleVocabulary.createTerm(key, key, value['title']) for
                (key, value) in terms
            ])

        user = get_valid_user()

        if user:
            user_groups = tuple(user.getGroups())
            user_has_sectors = tuple([
                group for group in user_groups
                if '-sector' in group
            ])

            # if user has no 'sector' assignments, return all codes
            # this results in sector experts having a filtered list while
            # other users (e.g. MS, LR) will see all codes.
            if user_has_sectors:
                return vocab_from_terms(*(
                    (term_key, term) for (term_key, term) in
                    nfr_codes().items() if validate_term(
                        build_prefix(LDAP_SECTOREXP, term['ldap']),
                        user_groups
                    )
                ))

        return vocab_from_terms(*nfr_codes().items())


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
