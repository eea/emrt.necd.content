import logging

from zope.component.hooks import getSite

from Products.CMFCore.utils import getToolByName

from emrt.necd.content.constants import LDAP_LEADREVIEW
from emrt.necd.content.constants import LDAP_SECRETARIAT
from emrt.necd.content.constants import LDAP_SECTOREXP
from emrt.necd.content.constants import ROLE_LR
from emrt.necd.content.constants import ROLE_SE

LOGGER = logging.getLogger("emrt.necd.content.setuphandlers")


LDAP_ROLE_MAPPING = {
    LDAP_SECTOREXP: ROLE_SE,
    LDAP_LEADREVIEW: ROLE_LR,
    LDAP_SECRETARIAT: "Manager",
}

LDAP_PLUGIN_ID = "ldap-plugin"
MEMCACHED_ID = "memcached"


def setup_memcached(portal, memcached_id):
    if memcached_id not in list(portal.keys()):
        try:
            _ = portal.manage_addProduct[
                "MemcachedManager"
            ].manage_addMemcachedManager(memcached_id)
        except Exception as err:
            LOGGER.exception(err)
        else:
            cache = portal[memcached_id]
            cache._settings["servers"] = ("127.0.0.1:11211",)
            cache._p_changed = True


def get_portal_acl(portal):
    return portal["acl_users"]


def get_ldap_plugin(acl, ldap_id):
    return acl[ldap_id]


def map_ldap_roles(context):
    """Map LDAP roles to Plone roles."""
    if context.readDataFile("emrt.necd.content_various.txt") is None:
        return
    portal_acl = get_portal_acl(getSite())
    ldap_plugin = get_ldap_plugin(portal_acl, LDAP_PLUGIN_ID)
    ldap_acl = ldap_plugin._getLDAPUserFolder()
    for ldap_group, plone_role in list(LDAP_ROLE_MAPPING.items()):
        ldap_acl.manage_addGroupMapping(ldap_group, plone_role)


def setup_ldap(portal, ldap_id, memcached_id):
    acl = get_portal_acl(portal)
    ldap_plugin = get_ldap_plugin(acl, ldap_id)

    # map LDAP roles to Plone roles
    ldap_acl = ldap_plugin._getLDAPUserFolder()
    for ldap_group, plone_role in list(LDAP_ROLE_MAPPING.items()):
        ldap_acl.manage_addGroupMapping(ldap_group, plone_role)

    # enable memcached
    ldap_plugin.ZCacheable_setManagerId(manager_id=memcached_id)

    # disable unnecessary PAS LDAP plugins
    enabled_interfaces = (
        "IUserEnumerationPlugin",
        "IGroupsPlugin",
        "IGroupEnumerationPlugin",
        "IRoleEnumerationPlugin",
        "IAuthenticationPlugin",
        "IPropertiesPlugin",
        "IRolesPlugin",
        "IGroupIntrospection",
        # Commenting out disabled plugins for reference.
        # 'ICredentialsResetPlugin',
        # 'IGroupManagement',
        # 'IUserAdderPlugin',
        # 'IUserManagement',
    )

    # activate selected plugins
    ldap_plugin.manage_activateInterfaces(enabled_interfaces)

    # move LDAP Properties plugin to top
    plugins = acl["plugins"]
    active_plugins = plugins.getAllPlugins("IPropertiesPlugin")["active"]
    interface = plugins._getInterfaceFromName("IPropertiesPlugin")

    for _ in range(len(active_plugins) - 1):
        # need to move it one position at a time
        plugins.movePluginsUp(interface, [ldap_id])


def post_install(context):
    portal = getSite()
    setup_memcached(portal, MEMCACHED_ID)
    setup_ldap(portal, LDAP_PLUGIN_ID, MEMCACHED_ID)


def setupVarious(context):
    """Various import steps for emrt.necd.content."""
    if context.readDataFile("emrt.necd.content_various.txt") is None:
        return


def update_workflow_rolemap(context):
    if context.readDataFile("emrt.necd.content_various.txt") is None:
        return

    site = context.getSite()
    portal_workflow = getToolByName(site, "portal_workflow")
    portal_workflow.updateRoleMappings()
