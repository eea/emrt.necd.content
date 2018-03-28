import itertools

from operator import itemgetter
from zope import schema
from zope.interface import implementer
from zope.interface import Interface
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary

from plone.i18n.normalizer.interfaces import IURLNormalizer
from plone.registry.interfaces import IRegistry

import plone.api as api

from emrt.necd.content import MessageFactory as _
from emrt.necd.content.constants import LDAP_SECTOREXP
from emrt.necd.content.constants import ROLE_LR

from emrt.necd.content.nfr_code_matching import INECDSettings
from emrt.necd.content.nfr_code_matching import nfr_codes


class INECDVocabularies(Interface):

    projection_pollutants = schema.Dict(
        title=_(u"Projection pollutants vocabulary"),
        description=_(u"Registers the values for pollutants in the context of "
                      u"a Projection ReviewFolder"),
        key_type=schema.TextLine(title=_(u"Pollutant key")),
        value_type=schema.TextLine(title=_(u"Pollutant value"),),
    )

    activity_data = schema.Dict(
        title=_(u"Activity data"),
        description=_(u"Registers the activity data"),
        key_type=schema.TextLine(title=_(u"Activity data type")),
        value_type=schema.List(value_type=schema.TextLine(
            title=_(u"Activity data"),
        ),)
    )


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

        terms = []

        if context.type == 'inventory':
            pvoc = api.portal.get_tool('portal_vocabularies')
            voc = pvoc.getVocabularyByName('pollutants')

            if voc is not None:
                for key, value in voc.getVocabularyLines():
                    # create a term - the arguments are the value, the token, and
                    # the title (optional)
                    terms.append(SimpleVocabulary.createTerm(key, key, value))

        else:
            registry = getUtility(IRegistry)
            pollutants = registry.forInterface(
                INECDVocabularies).projection_pollutants
            for key, value in pollutants.items():
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
                    nfr_codes(context).items() if validate_term(
                        build_prefix(LDAP_SECTOREXP, term['ldap']),
                        user_groups
                    )
                ))

        return vocab_from_terms(*nfr_codes(context).items())


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


@implementer(IVocabularyFactory)
class ActivityData(object):

    def __call__(self, context):
        registry = getUtility(IRegistry)
        normalizer = getUtility(IURLNormalizer).normalize

        activity_data = registry.forInterface(INECDVocabularies).activity_data

        activities = sorted(set(itertools.chain(*activity_data.values())))
        terms = [
            # SimpleTerm needs to have ascii encoded strings as keys.
            # The activity terms also include unicode symbols.
            # We URL-normalize the value in order to obtain a valid key.
            mk_term(normalizer(activity), activity)
            for activity in activities
        ]

        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class ActivityDataType(object):

    def __call__(self, context):
        registry = getUtility(IRegistry)
        activity_data = registry.forInterface(INECDVocabularies).activity_data

        terms = []

        for activity_type in activity_data.keys():
            terms.append(SimpleVocabulary.createTerm(activity_type))

        return SimpleVocabulary(terms)



