import csv
import itertools
from operator import itemgetter

from zope.component import getUtility
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary

from plone import api
from plone.i18n.normalizer.interfaces import IURLNormalizer
from plone.registry.interfaces import IRegistry

from emrt.necd.content.constants import LDAP_SECTOREXP
from emrt.necd.content.constants import ROLE_LR
from emrt.necd.content.constants import ROLE_MSA
from emrt.necd.content.constants import ROLE_MSE
from emrt.necd.content.constants import ROLE_SE
from emrt.necd.content.nfr_code_matching import INECDSettings
from emrt.necd.content.nfr_code_matching import nfr_codes
from emrt.necd.content.utilities.interfaces import IGetLDAPWrapper

from .interfaces import INECDVocabularies


def get_valid_user():
    try:
        user = api.user.get_current()
    except Exception:
        return None

    return user if user and not api.user.is_anonymous() else None


def validate_term(prefix, groups):
    return tuple([group for group in groups if group.startswith(prefix)])


def build_prefix(ldap_role, sector):
    return "{}-{}-".format(ldap_role, sector)


def vocab_from_terms(*terms):
    return SimpleVocabulary(
        [
            SimpleVocabulary.createTerm(key, key, value["title"])
            for (key, value) in terms
        ]
    )


def check_user_for_vocab(context, user):
    user_roles = api.user.get_roles(obj=context)
    user_groups = tuple(user.getGroups())
    user_has_sectors = tuple(
        [group for group in user_groups if "-sector" in group]
    )
    user_is_lr_or_manager = set(user_roles).intersection((ROLE_LR, "Manager"))

    # if user has no 'sector' assignments, return all codes
    # this results in sector experts having a filtered list while
    # other users (e.g. MS, LR) will see all codes.
    return not user_is_lr_or_manager and user_has_sectors


def mk_term(key, value):
    return SimpleVocabulary.createTerm(key, key, value)


def csv_entries(data: str):
    data = data.strip()
    if data:
        for key, value in csv.reader(data.split("\n")):
            yield key, value


def csv_to_terms(data: str):
    return [
        mk_term(key, value)
        for key, value in csv_entries(data)
    ]


def vocabulary_from_csv_string(data: str):
    return SimpleVocabulary(csv_to_terms(data))


def get_registry_interface_field_data(interface, field):
    registry = getUtility(IRegistry)
    registry_data = registry.forInterface(interface)

    return registry_data.__getattr__(field)


@implementer(IVocabularyFactory)
class MSVocabulary(object):
    def __call__(self, context):
        csv_data = get_registry_interface_field_data(
            INECDVocabularies, "eea_member_states"
        )
        return vocabulary_from_csv_string(csv_data)


@implementer(IVocabularyFactory)
class GHGSourceCategory(object):
    def __call__(self, context):
        csv_data = get_registry_interface_field_data(
            INECDVocabularies, "ghg_source_category"
        )
        return vocabulary_from_csv_string(csv_data)


@implementer(IVocabularyFactory)
class GHGSourceSectors(object):
    def __call__(self, context):
        csv_data = get_registry_interface_field_data(
            INECDVocabularies, "ghg_source_sectors"
        )
        return vocabulary_from_csv_string(csv_data)


@implementer(IVocabularyFactory)
class Pollutants(object):
    def __call__(self, context):
        terms = []

        if context.type == "inventory":
            csv_data = get_registry_interface_field_data(
                INECDVocabularies, "pollutants"
            )
            return vocabulary_from_csv_string(csv_data)

        else:
            pollutants = get_registry_interface_field_data(
                INECDVocabularies, "projection_pollutants"
            )

            for key, value in list(pollutants.items()):
                terms.append(SimpleVocabulary.createTerm(key, key, value))

        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class Fuel(object):
    def __call__(self, context):
        csv_data = get_registry_interface_field_data(INECDVocabularies, "fuel")
        return vocabulary_from_csv_string(csv_data)


@implementer(IVocabularyFactory)
class Highlight(object):
    def __call__(self, context, voc_name=None):
        if voc_name is None:
            if context.highlight_vocabulary:
                voc_name = context.highlight_vocabulary
            else:
                voc_name = (
                    'highlight' if context.type == 'inventory'
                    else 'highlight_projection'
                )

        csv_data = get_registry_interface_field_data(
            INECDVocabularies, voc_name
        )
        return vocabulary_from_csv_string(csv_data)


@implementer(IVocabularyFactory)
class HighlightVocabularyTypes(object):
    def __call__(self, context):
        default_term = mk_term(
            '',
            'Default: Projection or Inventory pre 2024'
        )

        csv_data = get_registry_interface_field_data(
            INECDVocabularies, 'highlight_vocabulary_types'
        )
        terms = itertools.chain([default_term], csv_to_terms(csv_data))
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class Parameter(object):
    def __call__(self, context):
        terms = []

        if context.type == "inventory":
            csv_data = get_registry_interface_field_data(
                INECDVocabularies, "parameter"
            )
            return vocabulary_from_csv_string(csv_data)

        else:
            pollutants = get_registry_interface_field_data(
                INECDVocabularies, "projection_parameter"
            )
            try:
                tool_id = context.get_review_folder().getId()
            except AttributeError:
                tool_id = None

            for pol in pollutants:
                key = pol["key"]
                label = pol["label"]

                if tool_id:
                    disabled = pol.get("disabled", "").split(",")
                    if tool_id and tool_id in disabled:
                        continue

                terms.append(SimpleVocabulary.createTerm(key, key, label))

        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class NFRCode(object):
    def __call__(self, context):
        user = get_valid_user()

        if user:
            ldap_wrapper = getUtility(IGetLDAPWrapper)(context)
            user_groups = tuple(user.getGroups())
            vocab_with_validate = check_user_for_vocab(context, user)
            if vocab_with_validate:
                return vocab_from_terms(
                    *(
                        (term_key, term)
                        for (term_key, term) in list(
                        nfr_codes(context).items()
                    )
                        if validate_term(
                        build_prefix(
                            ldap_wrapper(LDAP_SECTOREXP), term["ldap"]
                        ),
                        user_groups,
                    )
                    )
                )

        return vocab_from_terms(*list(nfr_codes(context).items()))


@implementer(IVocabularyFactory)
class NFRCodeInventories(object):
    def __call__(self, context):
        user = get_valid_user()

        if user:
            ldap_wrapper = getUtility(IGetLDAPWrapper)(context)
            user_groups = tuple(user.getGroups())
            vocab_with_validate = check_user_for_vocab(context, user)
            registry_field = "nfrcodeMapping_projection_inventory"
            if vocab_with_validate:
                return vocab_from_terms(
                    *(
                        (term_key, term)
                        for (term_key, term) in list(
                        nfr_codes(context, field=registry_field).items()
                    )
                        if validate_term(
                        build_prefix(
                            ldap_wrapper(LDAP_SECTOREXP), term["ldap"]
                        ),
                        user_groups,
                    )
                    )
                )

        return vocab_from_terms(
            *list(
                nfr_codes(
                    context, "nfrcodeMapping_projection_inventory"
                ).items()
            )
        )


@implementer(IVocabularyFactory)
class Conclusions(object):
    def __call__(self, context):
        csv_data = get_registry_interface_field_data(
            INECDVocabularies, "conclusion_reasons"
        )
        return vocabulary_from_csv_string(csv_data)


@implementer(IVocabularyFactory)
class SectorNames(object):
    def __call__(self, context):
        sectorNames = get_registry_interface_field_data(
            INECDSettings, "sectorNames"
        )

        return SimpleVocabulary(
            [
                mk_term(sector, name)
                for sector, name in sorted(
                list(sectorNames.items()), key=itemgetter(0)
            )
            ]
        )


@implementer(IVocabularyFactory)
class ActivityData(object):
    def __call__(self, context):
        normalizer = getUtility(IURLNormalizer).normalize

        activity_data = get_registry_interface_field_data(
            INECDVocabularies, "activity_data"
        )
        activities = sorted(
            set(itertools.chain(*list(activity_data.values())))
        )
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
        activity_data = get_registry_interface_field_data(
            INECDVocabularies, "activity_data"
        )
        terms = []

        for activity_type in list(activity_data.keys()):
            terms.append(SimpleVocabulary.createTerm(activity_type))

        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class ScenarioType(object):
    def __call__(self, context):
        csv_data = get_registry_interface_field_data(
            INECDVocabularies, "scenario_type"
        )
        return vocabulary_from_csv_string(csv_data)


@implementer(IVocabularyFactory)
class Roles(object):
    def __call__(self, context):
        terms = list(
            itertools.starmap(
                mk_term,
                [
                    ("Manager", "Manager"),
                    (ROLE_SE, "Sector Expert"),
                    (ROLE_LR, "Lead Reviewer"),
                    (ROLE_MSA, "MS Authority"),
                    (ROLE_MSE, "MS Expert"),
                ],
            )
        )

        return SimpleVocabulary(terms)
