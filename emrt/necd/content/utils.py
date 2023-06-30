import concurrent.futures
import json
import string
from itertools import chain
from operator import itemgetter
from typing import Optional
from typing import cast

from OFS.Traversable import Traversable

from Acquisition import aq_parent
from zope.component import getUtility
from zope.interface.interface import Specification
from zope.schema.interfaces import IVocabularyFactory

from plone import api

from emrt.necd.content.utilities.ldap_wrapper import ldap_inventory


def user_has_ldap_role(
    ldap_name, user=None, groups=None, ldap_wrapper=ldap_inventory
):
    _user = user if user else api.user.get_current()
    _groups = groups if groups else _user.getGroups()
    return any(
        tuple(
            group
            for group in _groups
            if group.startswith(ldap_wrapper(ldap_name))
        )
    )


def get_user_sectors(user):
    return set(
        chain(
            *[
                [n for n in g.split("-") if "sector" in n and n[-1].isdigit()]
                for g in user.getGroups()
            ]
        )
    )


def principals_with_roles(context, rolenames):
    def match_roles(roles):
        return tuple(set(roles).intersection(rolenames))

    def filter_entry(entry):
        principal = itemgetter(0)
        roles = itemgetter(1)
        return principal(entry) if match_roles(roles(entry)) else None

    principals = list(map(filter_entry, context.get_local_roles()))
    return tuple(filter(bool, principals))


def find_parent_with_interface(
    interface: Specification, context: Traversable
) -> Optional[Traversable]:
    if interface.providedBy(context):
        return context
    elif parent := cast(Optional[Traversable], aq_parent(context)):
        return find_parent_with_interface(interface, parent)
    else:
        return None


def concurrent_loop(workers, timeout, func, items, *args):
    """Run as:
    my_concurrent = partial(utils.concurrent_loop, 32, 600.0)
    result = my_concurrent(lambda item: ..., [item, item, ...]).
    """
    results = []
    tpe = concurrent.futures.ThreadPoolExecutor
    with tpe(max_workers=workers) as executor:
        futures = [executor.submit(func, item, *args) for item in items]
        for idx, future in enumerate(
            concurrent.futures.as_completed(futures, timeout=timeout)
        ):
            results.append(future.result())
    return results


def append_string(sep, base, tail):
    return "{}{}{}".format(base, sep, tail)


HIDDEN_ACTIONS = [
    "/content_status_history",
    "/placeful_workflow_configuration",
]


def hidden(menuitem):
    for action in HIDDEN_ACTIONS:
        if menuitem.get("action").endswith(action):
            return True
    return False


def get_vocabulary_value(context, vocabulary, term):
    vocab_factory = getUtility(IVocabularyFactory, name=vocabulary)
    vocabulary = vocab_factory(context)
    if not term:
        return ""
    try:
        value = vocabulary.getTerm(term)
        return value.title
    except LookupError:
        return term


def jsonify(request, data, cache=False, sort_keys=True, indent=2):
    header = request.RESPONSE.setHeader
    header("Content-Type", "application/json")
    if cache:
        header("Expires", "Sun, 17-Jan-2038 19:14:07 GMT")
    return json.dumps(data, indent=indent, sort_keys=sort_keys)


def reduce_text(text, limit):
    if len(text) <= limit:
        return text
    new_text = text[:limit]
    new_text_split = new_text.split(" ")
    slice_size = -1 if len(new_text_split) > 1 else 1
    clean_text = " ".join(new_text_split[:slice_size])

    if clean_text[-1] in string.punctuation:
        clean_text = clean_text[:-1]

    if isinstance(clean_text, str):
        return "{0}...".format(clean_text)
    else:
        return "{0}...".format(clean_text.decode("utf-8"))


def format_date(date, fmt="%d %b %Y, %H:%M CET"):
    return date.strftime(fmt)
