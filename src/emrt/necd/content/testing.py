# -*- coding: utf-8 -*-
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import List

from Products.CMFPlone.Portal import PloneSite

from plone import api
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import TEST_USER_ID
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.app.testing import setRoles
from plone.testing import z2

import emrt.necd.content
from emrt.necd.content import constants as C
from emrt.necd.content.setuphandlers import LDAP_PLUGIN_ID


@dataclass
class TestUser:
    """Keeps user information."""
    name: str
    password: str
    email: str
    roles: List[str]


def pwgen():
    """Generate a random 8 character password."""
    return uuid.uuid4().hex[:8]


class USERS(Enum):
    """The application users. For easy reference."""
    SE = TestUser("user_se", pwgen(), "user-se@eaudeweb.ro", [C.ROLE_SE])
    MSE = TestUser("user_mse", pwgen(), "user-mse@eaudeweb.ro", [C.ROLE_MSE])
    MSA = TestUser("user_msa", pwgen(), "user-msa@eaudeweb.ro", [C.ROLE_MSA])
    LR = TestUser("user_lr", pwgen(), "user-lr@eaudeweb.ro", [C.ROLE_LR])
    CP = TestUser("user_cp", pwgen(), "user-cp@eaudeweb.ro", [C.ROLE_CP])


class EmrtNecdContentLayer(PloneSandboxLayer):
    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        import plone.app.dexterity

        self.loadZCML(package=plone.app.dexterity)
        import plone.restapi

        self.loadZCML(package=plone.restapi)
        import pas.plugins.ldap

        self.loadZCML(package=pas.plugins.ldap)
        self.loadZCML(package=pas.plugins.ldap.plonecontrolpanel)
        import collective.z3cform.datagridfield

        self.loadZCML(package=collective.z3cform.datagridfield)
        import collective.deletepermission

        self.loadZCML(package=collective.deletepermission)
        import yafowil.plone

        self.loadZCML(package=yafowil.plone)
        self.loadZCML(package=emrt.necd.content)

    def setUpPloneSite(self, portal: PloneSite):
        applyProfile(portal, "emrt.necd.content:default")

        # remove ldap plugin for tests
        pas = portal["acl_users"]
        del pas[LDAP_PLUGIN_ID]

        setRoles(portal, TEST_USER_ID, ["Manager"])

        for u in USERS:
            userdef = u.value
            print(userdef.roles)
            with api.env.adopt_roles(roles=["Manager"]):
                api.user.create(
                    email=userdef.email,
                    username=userdef.name,
                    password=userdef.password,
                    roles=userdef.roles,
                )
            # pas.source_users.addUser(userdef.name, userdef.name, userdef.password)
            # for role in userdef.roles:
            #     pas.portal_role_manager.doAssignRoleToPrincipal(userdef.name, role)
            # user = api.user.get(userdef.name)
            # user.setMemberProperties({"email": userdef.email})


EMRT_NECD_CONTENT_FIXTURE = EmrtNecdContentLayer()


EMRT_NECD_CONTENT_INTEGRATION_TESTING = IntegrationTesting(
    bases=(EMRT_NECD_CONTENT_FIXTURE,),
    name="EmrtNecdContentLayer:IntegrationTesting",
)


EMRT_NECD_CONTENT_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(EMRT_NECD_CONTENT_FIXTURE,),
    name="EmrtNecdContentLayer:FunctionalTesting",
)


EMRT_NECD_CONTENT_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        EMRT_NECD_CONTENT_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE,
    ),
    name="EmrtNecdContentLayer:AcceptanceTesting",
)
