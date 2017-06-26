from operator import itemgetter
from zope.interface import implementer
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary

from plone.registry.interfaces import IRegistry

import plone.api as api

from emrt.necd.content.constants import LDAP_SECTOREXP
from emrt.necd.content.constants import ROLE_LR

from emrt.necd.content.nfr_code_matching import INECDSettings
from emrt.necd.content.nfr_code_matching import nfr_codes


def mk_term(key, value):
    return SimpleVocabulary.createTerm(key, key, value)


@implementer(IVocabularyFactory)
class MSVocabulary(object):

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


@implementer(IVocabularyFactory)
class GHGSourceCategory(object):

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


@implementer(IVocabularyFactory)
class GHGSourceSectors(object):

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


@implementer(IVocabularyFactory)
class Pollutants(object):

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


@implementer(IVocabularyFactory)
class Fuel(object):

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


@implementer(IVocabularyFactory)
class Highlight(object):

    def __call__(self, context):
        pvoc = api.portal.get_tool('portal_vocabularies')
        voc = pvoc.getVocabularyByName('highlight')
        if voc is None:
            return SimpleVocabulary([])

        terms = [mk_term(*pair) for pair in voc.getVocabularyLines()]
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class Parameter(object):

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


@implementer(IVocabularyFactory)
class StatusFlag(object):

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


@implementer(IVocabularyFactory)
class NFRCode(object):

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
            user_roles = api.user.get_roles(obj=context)
            user_groups = tuple(user.getGroups())
            user_has_sectors = tuple([
                group for group in user_groups
                if '-sector' in group
            ])
            user_is_lr_or_manager = set(user_roles).intersection(
                (ROLE_LR, 'Manager'))

            # if user has no 'sector' assignments, return all codes
            # this results in sector experts having a filtered list while
            # other users (e.g. MS, LR) will see all codes.
            if not user_is_lr_or_manager and user_has_sectors:
                return vocab_from_terms(*(
                    (term_key, term) for (term_key, term) in
                    nfr_codes().items() if validate_term(
                        build_prefix(LDAP_SECTOREXP, term['ldap']),
                        user_groups
                    )
                ))

        return vocab_from_terms(*nfr_codes().items())


@implementer(IVocabularyFactory)
class Conclusions(object):

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


@implementer(IVocabularyFactory)
class SectorNames(object):

    def __call__(self, context):
        registry = getUtility(IRegistry)
        sectorNames = registry.forInterface(INECDSettings).sectorNames

        return SimpleVocabulary([
            mk_term(sector, name)
            for sector, name
            in sorted(sectorNames.items(), key=itemgetter(0))
        ])
