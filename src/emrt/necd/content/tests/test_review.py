# -*- coding: utf-8 -*-
"""Setup tests for this package."""
import unittest

from zope.component import getMultiAdapter

from plone import api
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles

from emrt.necd.content.testing import (  # noqa: E501
    EMRT_NECD_CONTENT_INTEGRATION_TESTING,
)


class TestSetup(unittest.TestCase):
    """Test that emrt.necd.content is properly installed."""

    layer = EMRT_NECD_CONTENT_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.request = self.layer["request"]
        self.tool = api.content.create(
            container=self.portal,
            type="ReviewFolder",
            title="Test review",
            tableau_statistics="nothing",
            tableau_statistics_roles=list(["Manager"]),
        )
        self.tool.type = "inventory"
        api.content.transition(obj=self.tool, transition="publish")
        api.content.transition(obj=self.tool, transition="start")

    def test_view(self):
        view = getMultiAdapter((self.tool, self.portal.REQUEST), name="view")
        content = view()
        self.assertTrue("Test review" in content)
        self.assertTrue("Overview list" in content)
        self.assertTrue("New observation" in content)
        self.assertTrue("observations-table" in content)

    def test_add_observation(self):
        observation = api.content.create(
            container=self.tool,
            type="Observation",
            title="",
            text="observation description",
            country="at",
            nfr_code="1A1",
            year="2022",
            pollutants=list(["SO2"]),
            review_year=2023,
            ms_key_category=True,
            parameter=list(["act", "emi"]),
        )
        self.assertEqual(observation.getId(), "AT-1A1-2023-0001")
        view = getMultiAdapter((observation, self.portal.REQUEST), name="view")
        content = view()
        self.assertTrue("AT-1A1-2023-0001" in content)
        self.assertTrue("Austria" in content)
        self.assertTrue("1A1 Energy production" in content)
        self.assertTrue("SO2" in content)
        self.assertTrue("2023" in content)
        self.assertTrue("2022" in content)
        self.assertTrue("observation description" in content)
        self.assertTrue("Emission" in content)
        self.assertTrue("Activity data" in content)
        self.assertTrue("MS Key category" in content)
        self.assertTrue("Draft observation" in content)
        self.assertTrue("Add question" in content)
        self.assertTrue("Edit observation" in content)
        self.assertTrue("Delete observation" in content)
        self.assertTrue("Go to conclusions" in content)
