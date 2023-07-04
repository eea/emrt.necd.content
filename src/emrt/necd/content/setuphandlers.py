# -*- coding: utf-8 -*-
import logging

from Products.CMFPlone.interfaces import INonInstallable
from zope.interface import implementer

from plone import api


LOGGER = logging.getLogger("emrt.necd.content.setuphandlers")

LDAP_PLUGIN_ID = "pasldap"


@implementer(INonInstallable)
class HiddenProfiles(object):

    def getNonInstallableProfiles(self):
        """Hide uninstall profile from site-creation and quickinstaller."""
        return [
            "emrt.necd.content:uninstall",
        ]

    def getNonInstallableProducts(self):
        """Hide the upgrades package from site-creation and quickinstaller."""
        return ["emrt.necd.content.upgrades"]


def get_portal_acl(portal):
    return portal["acl_users"]


def get_ldap_plugin(acl, ldap_id):
    return acl[ldap_id]


def setup_ldap(portal, ldap_id):
    acl = get_portal_acl(portal)
    try:
        ldap_plugin = get_ldap_plugin(acl, ldap_id)
    except KeyError:
        LOGGER.warn("LDAP Plugin not found. LDAP setup skipped.")

    # disable unnecessary PAS LDAP plugins
    enabled_interfaces = (
        "IUserEnumerationPlugin",
        "IGroupsPlugin",
        "IGroupEnumerationPlugin",
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
    """Post install script"""
    setup_ldap(api.portal.get(), LDAP_PLUGIN_ID)


def uninstall(context):
    """Uninstall script"""
    # Do something at the end of the uninstallation of this package.


def update_workflow_rolemap(context):
    portal_workflow = api.portal.get_tool("portal_workflow")
    portal_workflow.updateRoleMappings()
