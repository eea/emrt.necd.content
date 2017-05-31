import concurrent.futures
from operator import itemgetter
import plone.api as api


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
