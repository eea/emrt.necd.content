# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from emrt.necd.content.testing import (  # noqa: E501
    EMRT_NECD_CONTENT_INTEGRATION_TESTING,
)
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID

import unittest


try:
    from Products.CMFPlone.utils import get_installer
except ImportError:
    get_installer = None


class TestSetup(unittest.TestCase):
    """Test that emrt.necd.content is properly installed."""

    layer = EMRT_NECD_CONTENT_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        if get_installer:
            self.installer = get_installer(self.portal, self.layer['request'])
        else:
            self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_product_installed(self):
        """Test if emrt.necd.content is installed."""
        self.assertTrue(self.installer.is_product_installed(
            'emrt.necd.content'))

    def test_browserlayer(self):
        """Test that IEmrtNecdContentLayer is registered."""
        from emrt.necd.content.interfaces import IEmrtNecdContentLayer
        from plone.browserlayer import utils
        self.assertIn(
            IEmrtNecdContentLayer,
            utils.registered_layers())


class TestUninstall(unittest.TestCase):

    layer = EMRT_NECD_CONTENT_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        if get_installer:
            self.installer = get_installer(self.portal, self.layer['request'])
        else:
            self.installer = api.portal.get_tool('portal_quickinstaller')
        roles_before = api.user.get_roles(TEST_USER_ID)
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.installer.uninstall_product('emrt.necd.content')
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if emrt.necd.content is cleanly uninstalled."""
        self.assertFalse(self.installer.is_product_installed(
            'emrt.necd.content'))

    def test_browserlayer_removed(self):
        """Test that IEmrtNecdContentLayer is removed."""
        from emrt.necd.content.interfaces import IEmrtNecdContentLayer
        from plone.browserlayer import utils
        self.assertNotIn(IEmrtNecdContentLayer, utils.registered_layers())
