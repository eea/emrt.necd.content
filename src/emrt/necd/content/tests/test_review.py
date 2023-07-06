# -*- coding: utf-8 -*-
"""Setup tests for this package."""
import unittest
from typing import TypeVar
from typing import cast

from zope.component import getMultiAdapter

from plone import api
from plone.app.testing import TEST_USER_ID
from plone.app.testing import helpers
from plone.app.testing import setRoles

from emrt.necd.content.comment import EditForm as CommentEditForm
from emrt.necd.content.observation import AddView as ObservationAddView
from emrt.necd.content.observation import Observation
from emrt.necd.content.observation import ObservationView
from emrt.necd.content.question import AddView as QuestionAddView
from emrt.necd.content.question import Question
from emrt.necd.content.commentanswer import CommentAnswer
from emrt.necd.content.commentanswer import AddView as CommentAnswerAddView
from emrt.necd.content.reviewfolder import ReviewFolder
from emrt.necd.content.testing import (  # noqa: E501
    EMRT_NECD_CONTENT_INTEGRATION_TESTING,
)
from emrt.necd.content.testing import USERS

TEST_USER_EMAIL = "test-user@eaudeweb.ro"

T = TypeVar("T")


class TestSetup(unittest.TestCase):
    """Test that emrt.necd.content is properly installed."""

    layer = EMRT_NECD_CONTENT_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        self.mailhost = self.portal.MailHost
        self.portal.email_from_address = "test-portal@devel.enisa.edw.ro"
        api.user.get_current().setMemberProperties({"email": TEST_USER_EMAIL})
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.request = self.layer["request"]
        self.tool: ReviewFolder = api.content.create(
            container=self.portal,
            type="ReviewFolder",
            title="Test review",
            tableau_statistics="nothing",
            tableau_statistics_roles=list(["Manager"]),
        )
        self.tool.type = "inventory"
        api.content.transition(obj=self.tool, transition="publish")
        api.content.transition(obj=self.tool, transition="start")

    def tearDown(self) -> None:
        self.request.form = {}

    def create_observation(self) -> Observation:
        add_view: ObservationAddView = cast(
            ObservationAddView,
            self.tool.restrictedTraverse("++add++Observation"),
        )
        form = add_view.form_instance
        form_data = {
            "text": "observation description",
            "country": "at",
            "nfr_code": "1A1",
            "year": "2022",
            "pollutants": list(["SO2"]),
            "review_year": 2023,
            "ms_key_category": True,
            "parameter": list(["act", "emi"]),
        }
        observation = cast(Observation, form.createAndAdd(data=form_data))
        return cast(Observation, self.tool[observation.getId()])
    
    def create_answer(self, question: Question, text="") -> CommentAnswer:
        add_view: CommentAnswerAddView = cast(
            CommentAnswerAddView,
            question.restrictedTraverse("++add++CommentAnswer"),
        )
        self.request.form["form.widgets.text"] = text
        answer = cast(CommentAnswer, add_view.form_instance.createAndAdd(data=None))
        return cast(CommentAnswer, question[answer.getId()])

    def create_question(self, observation: Observation, text: str = ""):
        add_view: QuestionAddView = cast(
            QuestionAddView, observation.restrictedTraverse("++add++Question")
        )
        self.request.form["form.widgets.text"] = text
        added = cast(Question, add_view.form_instance.createAndAdd(data=None))
        return cast(Question, observation[added.getId()])

    def get_view(self, context, cls: T, name: str = "view") -> T:
        return cast(
            cls,
            getMultiAdapter((context, self.request), name=name),
        )

    def test_view(self):
        view = getMultiAdapter((self.tool, self.request), name="view")
        content = view()
        self.assertTrue("Test review" in content)
        self.assertTrue("Overview list" in content)
        self.assertTrue("New observation" in content)
        self.assertTrue("observations-table" in content)

    def test_add_observation(self):
        add_view: ObservationAddView = cast(
            ObservationAddView,
            self.tool.restrictedTraverse("++add++Observation"),
        )
        form = add_view.form_instance
        form_data = {
            "text": "observation description",
            "country": "at",
            "nfr_code": "1A1",
            "year": "2022",
            "pollutants": list(["SO2"]),
            "review_year": 2023,
            "ms_key_category": True,
            "parameter": list(["act", "emi"]),
        }
        observation = cast(Observation, form.createAndAdd(data=form_data))
        self.assertEqual(observation.getId(), "AT-1A1-2023-0001")
        observation = cast(Observation, self.tool[observation.getId()])
        view = self.get_view(observation, ObservationView)
        content = cast(str, view())
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

    def test_add_question(self):
        observation = self.create_observation()
        self.assertIsNone(observation.get_question())
        self.create_question(observation, "question text")
        question = observation.get_question()
        self.assertIsInstance(question, Question)
        view = self.get_view(observation, ObservationView)
        content = view()
        self.assertTrue("question text" in content)

    def test_edit_question(self):
        observation = self.create_observation()
        question = self.create_question(observation, "question text")
        comment = question.getFirstComment()
        edit_form = self.get_view(comment, CommentEditForm, name="edit")
        _: str = edit_form()  # needed to initialize the form
        edit_form.applyChanges({"text": "question text - modified"})
        content = self.get_view(observation, ObservationView)()
        self.assertTrue("question text - modified" in content)

    def test_se_observation_view(self):
        helpers.login(self.portal, USERS.SE.value.name)
        observation = self.create_observation()

        question = self.create_question(observation, "question text")
        self.assertIn(USERS.SE.value.name, question.creators)

        content: str = self.get_view(observation, ObservationView)()
        self.assertFalse("Create answer" in content)
        self.assertTrue("Send Question for Approval" in content)

    def test_question_workflow(self):
        helpers.login(self.portal, USERS.SE.value.name)
        observation = self.create_observation()
        question = self.create_question(observation, "question text")

        # request approval
        api.content.transition(obj=question, transition="send-to-lr")
        self.assertTrue("Recall Question" in self.get_view(observation, ObservationView)())

        # LR approves
        helpers.login(self.portal, USERS.LR.value.name)
        comment = question.getFirstComment()
        comment.restrictedTraverse("approve-question")()

        # SE Doesn't see "Recall question"
        helpers.login(self.portal, USERS.SE.value.name)
        self.assertFalse("Recall Question" in self.get_view(observation, ObservationView)())

        # SE Doesn't see "Recall question"
        helpers.login(self.portal, USERS.SE.value.name)
        self.assertFalse("Recall Question" in self.get_view(observation, ObservationView)())

        # MSA Gives answer
        helpers.login(self.portal, USERS.MSA.value.name)
        self.create_answer(question, text="The MSA answer")
        self.assertTrue("The MSA answer" in self.get_view(observation, ObservationView)())
