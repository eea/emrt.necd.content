# -*- coding: utf-8 -*-
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2

import emrt.necd.content


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

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'emrt.necd.content:default')


EMRT_NECD_CONTENT_FIXTURE = EmrtNecdContentLayer()


EMRT_NECD_CONTENT_INTEGRATION_TESTING = IntegrationTesting(
    bases=(EMRT_NECD_CONTENT_FIXTURE,),
    name='EmrtNecdContentLayer:IntegrationTesting',
)


EMRT_NECD_CONTENT_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(EMRT_NECD_CONTENT_FIXTURE,),
    name='EmrtNecdContentLayer:FunctionalTesting',
)


EMRT_NECD_CONTENT_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        EMRT_NECD_CONTENT_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE,
    ),
    name='EmrtNecdContentLayer:AcceptanceTesting',
)
