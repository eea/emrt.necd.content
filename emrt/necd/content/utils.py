import concurrent.futures
import plone.api as api

from emrt.necd.content.vocabularies import get_registry_interface_field_data
from emrt.necd.content.vocabularies import INECDVocabularies
from operator import itemgetter
from z3c.form.interfaces import WidgetActionExecutionError
from zope.component import getUtility
from zope.interface import Invalid
from zope.schema.interfaces import IVocabularyFactory


def user_has_ldap_role(ldap_name, user=None, groups=None):
    _user = user if user else api.user.get_current()
    _groups = groups if groups else _user.getGroups()
    return any(tuple(
        group for group in _groups
        if group.startswith(ldap_name)
    ))


def principals_with_roles(context, rolenames):
    def match_roles(roles):
        return tuple(set(roles).intersection(rolenames))

    def filter_entry(entry):
        principal = itemgetter(0)
        roles = itemgetter(1)
        return principal(entry) if match_roles(roles(entry)) else None

    principals = map(filter_entry, context.get_local_roles())
    return tuple(filter(bool, principals))


def find_parent_with_interface(interface, context):
    parent = context.aq_parent
    if interface.providedBy(parent):
        return parent
    return find_parent_with_interface(interface, parent)


def concurrent_loop(workers, timeout, func, items, *args):
    """ Run as:
        my_concurrent = partial(utils.concurrent_loop, 32, 600.0)
        result = my_concurrent(lambda item: ..., [item, item, ...])
    """
    results = []
    tpe = concurrent.futures.ThreadPoolExecutor
    with tpe(max_workers=workers) as executor:
        futures = [executor.submit(func, item, *args) for item in items]
        for idx, future in enumerate(
                concurrent.futures.as_completed(futures, timeout=timeout)):
            results.append(future.result())
    return results


def append_string(sep, base, tail):
    return '{}{}{}'.format(base, sep, tail)


HIDDEN_ACTIONS = [
    '/content_status_history',
    '/placeful_workflow_configuration',
]


def hidden(menuitem):
    for action in HIDDEN_ACTIONS:
        if menuitem.get('action').endswith(action):
            return True
    return False


def get_vocabulary_value(context, vocabulary, term):

    vocab_factory = getUtility(IVocabularyFactory, name=vocabulary)
    vocabulary = vocab_factory(context)
    if not term:
        return u''
    try:
        value = vocabulary.getTerm(term)
        return value.title
    except LookupError:
        return term


def activity_data_validator(context, type, activity):
    if activity and not type:
        raise WidgetActionExecutionError('activity_data_type',
                                         Invalid(u"Please select a type of "
                                                 u"activity before selecting "
                                                 u"an activity")
                                         )
    elif not activity and type:
        raise WidgetActionExecutionError('activity_data',
                                         Invalid(u"Please select an activity"
                                                 u" after you've selected an "
                                                 u"activity type")
                                         )
    elif activity and type:
        activity_data_registry = get_registry_interface_field_data(
            INECDVocabularies,'activity_data')

        activity_data_values = [get_vocabulary_value
                                (context,
                                 'emrt.necd.content.activity_data', val)
                                for val in activity
                                ]

        if not all(activity in activity_data_registry[type]
                   for activity in activity_data_values):
            raise WidgetActionExecutionError('activity_data',
                                             Invalid(
                                                 u"The activities you selected"
                                                 u" do not correspond to the "
                                                 u"activity type. Please "
                                                 u"selected the appropiate "
                                                 u"values")
                                             )