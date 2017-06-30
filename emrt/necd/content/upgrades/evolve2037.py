from logging import getLogger

import plone.api as api


LOGGER = getLogger(__name__)


COPY_FROM = 'Delete objects'
PERMISSION = 'Delete portal content'


def run(_):
    catalog = api.portal.get_tool('portal_catalog')
    objects = get_objects(catalog, ('Conclusions', ))

    obj_len = len(objects)
    LOGGER.info('Found %s objects.', obj_len)

    for idx, obj in enumerate(objects, start=1):
        do_upgrade(obj)
        if idx % 50 == 0:
            LOGGER.info('Done %s/%s.', idx, obj_len)


def do_upgrade(obj):
    source = [
        r['name']
        for r in obj.rolesOfPermission(COPY_FROM)
        if r['selected']
    ]
    obj.manage_permission(PERMISSION, roles=source, acquire=0)

    LOGGER.info('Updated permissions on %s', obj.absolute_url())


def get_objects(catalog, portal_type):
    brains = catalog(portal_type=portal_type)
    return tuple(brain.getObject() for brain in brains)


