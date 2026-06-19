# -*- coding: utf-8 -*-
"""Setup tests for this package."""
import unittest
from unittest.mock import patch
from typing import TypeVar
from typing import cast

from DateTime import DateTime
from zExceptions import Unauthorized
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
from emrt.necd.content.conclusions import AddView as ConclusionsAddView
from emrt.necd.content.browser.statechange import AssignConclusionReviewerForm
from emrt.necd.content.reviewfolder import ReviewFolder
from emrt.necd.content.testing import (  # noqa: E501
    EMRT_NECD_CONTENT_INTEGRATION_TESTING,
)
from emrt.necd.content.testing import USERS
from emrt.necd.content.upgrades import to311
from emrt.necd.content.upgrades import to312

TEST_USER_EMAIL = "test-user@eaudeweb.ro"
MSA_AT_GROUP = "extranet-necd-review-countries-msa-at"
QUESTION_WORKFLOW = "esd-question-review-workflow"
MS_VISIBILITY_INDEXES = [
    "observation_sent_to_msc",
    "observation_sent_to_mse",
    "observation_already_replied",
    "observation_question_status",
]

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

    def create_observation_in(
        self, folder: ReviewFolder, review_year: int = 2023
    ) -> Observation:
        add_view: ObservationAddView = cast(
            ObservationAddView,
            folder.restrictedTraverse("++add++Observation"),
        )
        form = add_view.form_instance
        form_data = {
            "text": "observation description",
            "country": "at",
            "nfr_code": "1A1",
            "year": "2022",
            "pollutants": list(["SO2"]),
            "review_year": review_year,
            "ms_key_category": True,
            "parameter": list(["act", "emi"]),
        }
        observation = cast(Observation, form.createAndAdd(data=form_data))
        return cast(Observation, folder[observation.getId()])

    def create_observation(self) -> Observation:
        return self.create_observation_in(self.tool)

    def create_review_folder(self, title) -> ReviewFolder:
        with api.env.adopt_roles(["Manager"]):
            folder: ReviewFolder = api.content.create(
                container=self.portal,
                type="ReviewFolder",
                title=str(title),
                tableau_statistics="nothing",
                tableau_statistics_roles=list(["Manager"]),
            )
            folder.type = "inventory"
            api.content.transition(obj=folder, transition="publish")
            api.content.transition(obj=folder, transition="start")
        return folder

    def create_answer(self, question: Question, text="") -> CommentAnswer:
        add_view: CommentAnswerAddView = cast(
            CommentAnswerAddView,
            question.restrictedTraverse("++add++CommentAnswer"),
        )
        answer = cast(
            CommentAnswer,
            add_view.form_instance.createAndAdd(data={"text": text}),
        )
        return cast(CommentAnswer, question[answer.getId()])

    def create_question(self, observation: Observation, text: str = ""):
        add_view: QuestionAddView = cast(
            QuestionAddView, observation.restrictedTraverse("++add++Question")
        )
        added = cast(
            Question,
            add_view.form_instance.createAndAdd(data={"text": text}),
        )
        return cast(Question, observation[added.getId()])

    def create_conclusion(self, observation: Observation, text: str = ""):
        add_view: ConclusionsAddView = cast(
            ConclusionsAddView,
            observation.restrictedTraverse("++add++Conclusions"),
        )
        added = add_view.form_instance.createAndAdd(
            data={
                "closing_reason": "resolved",
                "text": text,
                "highlight": tuple(),
            }
        )
        return observation[added.id]

    def add_comment(self, question: Question, item_id: str, text: str):
        with api.env.adopt_roles(["Manager"]):
            question.invokeFactory(type_name="Comment", id=item_id)
        comment = question[item_id]
        comment.text = text
        return comment

    def add_answer(self, question: Question, item_id: str, text: str):
        with api.env.adopt_roles(["Manager"]):
            question.invokeFactory(type_name="CommentAnswer", id=item_id)
        answer = question[item_id]
        answer.text = text
        return answer

    def set_qa_date(self, item, value):
        item.creation_date = value
        item.modification_date = value
        item.setEffectiveDate(value)
        item.reindexObject()

    def set_review_folder_year(self, year):
        self.tool.title = str(year)
        self.tool.reindexObject()

    def set_workflow_history_year(self, obj, workflow_id, year):
        history = []
        for item in obj.workflow_history[workflow_id]:
            updated = item.copy()
            updated["time"] = DateTime(f"{year}/01/01 00:00 UTC")
            history.append(updated)
        obj.workflow_history[workflow_id] = tuple(history)
        obj.reindexObject()

    def force_question_state(self, question, state, year):
        wf = api.portal.get_tool("portal_workflow")[QUESTION_WORKFLOW]
        question.workflow_history[QUESTION_WORKFLOW] = tuple(
            question.workflow_history[QUESTION_WORKFLOW]
        ) + (
            {
                "comments": "Test force state",
                "actor": api.user.get_current().getId(),
                "time": DateTime(f"{year}/01/01 00:00 UTC"),
                "action": "test-force-state",
                "review_state": state,
            },
        )
        wf.updateRoleMappingsFor(question)
        question.reindexObject()

    def reindex_ms_visibility(self, observation):
        observation.reindexObject(idxs=MS_VISIBILITY_INDEXES)

    def create_stale_carried_over_question(self):
        helpers.login(self.portal, USERS.SE.value.name)
        observation = self.create_observation()
        question = self.create_question(observation, "Current TERT question")
        current_comment = question.getFirstComment()

        old_date = DateTime("2020/01/01 00:00 UTC")
        old_items = [
            self.add_comment(question, "old-comment-1", "Old TERT question 1"),
            self.add_answer(question, "old-answer-1", "Old MS answer 1"),
            self.add_comment(question, "old-comment-2", "Old TERT question 2"),
            self.add_answer(question, "old-answer-2", "Old MS answer 2"),
        ]
        for item in old_items:
            self.set_qa_date(item, old_date)

        self.set_qa_date(current_comment, DateTime())
        api.content.transition(
            obj=question,
            transition="send-to-lr",
            comment=current_comment.getId(),
        )

        helpers.login(self.portal, USERS.LR.value.name)
        current_comment.restrictedTraverse("approve-question")()

        return observation, question, current_comment

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

    def test_add_observation_without_ms_key_category(self):
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
            "parameter": list(["act", "emi"]),
        }
        observation = cast(Observation, form.createAndAdd(data=form_data))
        observation = cast(Observation, self.tool[observation.getId()])
        self.assertFalse(observation.ms_key_category)

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

    def test_current_year_unanswered_question_ignores_old_answers_for_msa_actions(self):
        observation, question, _current_comment = (
            self.create_stale_carried_over_question()
        )

        self.assertTrue(question.has_answers())
        self.assertTrue(question.unanswered_questions())
        self.assertFalse(question.one_pending_answer())

        helpers.login(self.portal, USERS.MSA.value.name)
        content = self.get_view(observation, ObservationView)()

        self.assertIn("Create answer", content)
        self.assertEqual(content.count("workflow_action=answer-to-lr"), 0)
        self.assertEqual(content.count("workflow_action=assign-answerer"), 0)

    def test_msa_myview_uses_review_folder_year_for_carried_over_answers(self):
        self.set_review_folder_year(2026)

        helpers.login(self.portal, USERS.SE.value.name)
        observation = self.create_observation()
        question = self.create_question(observation, "question text")
        api.content.transition(obj=question, transition="send-to-lr")

        helpers.login(self.portal, USERS.LR.value.name)
        question.getFirstComment().restrictedTraverse("approve-question")()

        helpers.login(self.portal, USERS.MSA.value.name)
        answer = self.create_answer(question, text="The old MSA answer")
        api.content.transition(
            obj=question,
            transition="answer-to-lr",
            comment=answer.getId(),
        )

        self.set_workflow_history_year(question, QUESTION_WORKFLOW, 2025)
        self.force_question_state(question, "draft", 2026)
        self.reindex_ms_visibility(observation)

        view = self.get_view(self.tool, object, name="inboxview")
        view.rolemap_observations = {}

        self.assertEqual(view.get_answers_sent_to_se_re(), [])

    def test_published_old_review_folder_exports_rows_for_msa(self):
        self.set_review_folder_year(2024)

        helpers.login(self.portal, USERS.SE.value.name)
        observation = self.create_observation()
        question = self.create_question(observation, "question text")
        api.content.transition(obj=question, transition="send-to-lr")

        helpers.login(self.portal, USERS.LR.value.name)
        question.getFirstComment().restrictedTraverse("approve-question")()
        self.set_workflow_history_year(question, QUESTION_WORKFLOW, 2024)
        self.reindex_ms_visibility(observation)

        setRoles(self.portal, USERS.LR.value.name, ["Manager"])
        api.content.transition(obj=self.tool, transition="end-review")

        helpers.login(self.portal, USERS.MSA.value.name)
        user = api.user.get_current()
        view = self.get_view(self.tool, object)
        with patch.object(user, "getGroups", return_value=[MSA_AT_GROUP]):
            exported_ids = [brain.getId for brain in view.get_questions()]

        self.assertEqual(exported_ids, [observation.getId()])

    def test_upgrade_reindexes_ms_visibility_against_review_folder_year(self):
        self.set_review_folder_year(2024)

        helpers.login(self.portal, USERS.SE.value.name)
        observation = self.create_observation()
        question = self.create_question(observation, "question text")
        api.content.transition(obj=question, transition="send-to-lr")

        helpers.login(self.portal, USERS.LR.value.name)
        question.getFirstComment().restrictedTraverse("approve-question")()
        self.set_workflow_history_year(question, QUESTION_WORKFLOW, 2024)

        with patch("emrt.necd.content.upgrades.to312.transaction.commit"):
            to312.run(None)

        catalog = api.portal.get_tool("portal_catalog")
        brain = catalog(getId=observation.getId())[0]
        self.assertTrue(brain.observation_sent_to_msc)

    def test_upgrade_reindexes_only_historical_candidate_observations(self):
        current_year = DateTime().year()
        self.set_review_folder_year(2024)
        current_tool = self.create_review_folder(current_year)

        helpers.login(self.portal, USERS.SE.value.name)
        historical_observation = self.create_observation()
        historical_question = self.create_question(
            historical_observation, "historical question"
        )
        api.content.transition(
            obj=historical_question, transition="send-to-lr"
        )

        current_observation = self.create_observation_in(
            current_tool, review_year=current_year
        )
        current_question = self.create_question(
            current_observation, "current question"
        )
        api.content.transition(obj=current_question, transition="send-to-lr")

        helpers.login(self.portal, USERS.LR.value.name)
        historical_question.getFirstComment().restrictedTraverse(
            "approve-question"
        )()
        current_question.getFirstComment().restrictedTraverse(
            "approve-question"
        )()
        self.set_workflow_history_year(
            historical_question, QUESTION_WORKFLOW, 2024
        )
        self.set_workflow_history_year(
            current_question, QUESTION_WORKFLOW, current_year
        )

        with patch(
            "emrt.necd.content.upgrades.to312._update_ms_visibility",
            wraps=to312._update_ms_visibility,
        ) as update_ms_visibility:
            with patch("emrt.necd.content.upgrades.to312.transaction.commit"):
                to312.run(None)

        indexed_paths = [
            "/".join(call.args[1].getPhysicalPath())
            for call in update_ms_visibility.call_args_list
        ]

        self.assertIn(
            "/".join(historical_observation.getPhysicalPath()),
            indexed_paths,
        )
        self.assertNotIn(
            "/".join(current_observation.getPhysicalPath()),
            indexed_paths,
        )

    def test_submit_answer_action_is_rendered_only_on_answer_item(self):
        helpers.login(self.portal, USERS.SE.value.name)
        observation = self.create_observation()
        question = self.create_question(observation, "question text")
        api.content.transition(obj=question, transition="send-to-lr")

        helpers.login(self.portal, USERS.LR.value.name)
        comment = question.getFirstComment()
        comment.restrictedTraverse("approve-question")()

        helpers.login(self.portal, USERS.MSA.value.name)
        answer = self.create_answer(question, text="The MSA answer")
        api.content.transition(obj=question, transition="add-answer")
        content = self.get_view(observation, ObservationView)()

        self.assertEqual(content.count("workflow_action=answer-to-lr"), 1)
        action_url = content.split("workflow_action=answer-to-lr", 1)[1]
        action_url = action_url.split("</a>", 1)[0]
        self.assertIn("comment={}".format(answer.getId()), action_url)
        self.assertNotIn(
            'comment={}"'.format(comment.getId()),
            action_url,
        )

    def test_upgrade_repairs_stale_pending_answer_drafting_question(self):
        observation, question, _current_comment = (
            self.create_stale_carried_over_question()
        )

        helpers.login(self.portal, USERS.MSA.value.name)
        api.content.transition(obj=question, transition="add-answer")
        question.reindexObject()
        self.assertEqual(
            api.content.get_state(question), "pending-answer-drafting"
        )

        with patch("emrt.necd.content.upgrades.to311.transaction.commit"):
            to311.run(None)

        self.assertEqual(api.content.get_state(question), "pending")
        content = self.get_view(observation, ObservationView)()
        self.assertIn("Create answer", content)
        self.assertEqual(content.count("workflow_action=answer-to-lr"), 0)

    def test_lr_cannot_go_to_conclusions_while_question_waits_for_approval(self):
        helpers.login(self.portal, USERS.SE.value.name)
        observation = self.create_observation()
        question = self.create_question(observation, "question text")
        api.content.transition(obj=question, transition="send-to-lr")

        helpers.login(self.portal, USERS.LR.value.name)
        self.assertFalse(observation.can_draft_conclusions())
        self.assertFalse(
            "Go to conclusions" in self.get_view(observation, ObservationView)()
        )

    def test_go_to_conclusions_shows_after_lr_recalls_question_in_normal_flow(self):
        helpers.login(self.portal, USERS.SE.value.name)
        observation = self.create_observation()
        question = self.create_question(observation, "question text")
        api.content.transition(obj=question, transition="send-to-lr")

        helpers.login(self.portal, USERS.LR.value.name)
        question.getFirstComment().restrictedTraverse("approve-question")()
        api.content.transition(
            obj=question,
            transition="recall-question-lr",
            comment=question.getFirstComment().getId(),
        )

        self.assertEqual(api.content.get_state(observation), "pending")
        self.assertEqual(api.content.get_state(question), "recalled-lr")
        helpers.login(self.portal, USERS.SE.value.name)
        self.assertIn(
            "Go to Conclusions",
            self.get_view(observation, ObservationView)(),
        )

    def test_se_can_create_conclusion_after_lr_recalls_question(self):
        helpers.login(self.portal, USERS.SE.value.name)
        observation = self.create_observation()
        question = self.create_question(observation, "question text")
        api.content.transition(obj=question, transition="send-to-lr")

        helpers.login(self.portal, USERS.LR.value.name)
        question.getFirstComment().restrictedTraverse("approve-question")()
        api.content.transition(
            obj=question,
            transition="recall-question-lr",
            comment=question.getFirstComment().getId(),
        )

        helpers.login(self.portal, USERS.SE.value.name)
        self.create_conclusion(observation, "draft conclusion text")

        self.assertEqual(api.content.get_state(observation), "conclusions")
        self.assertEqual(api.content.get_state(question), "closed")

    def test_go_to_conclusions_shows_after_lr_recalls_reopened_qa_question(self):
        helpers.login(self.portal, USERS.SE.value.name)
        observation = self.create_observation()
        question = self.create_question(observation, "question text")
        self.create_conclusion(observation, "draft conclusion text")
        api.content.transition(obj=observation, transition="reopen-qa-chat")
        api.content.transition(obj=question, transition="send-to-lr")

        helpers.login(self.portal, USERS.LR.value.name)
        question.getFirstComment().restrictedTraverse("approve-question")()
        api.content.transition(
            obj=question,
            transition="recall-question-lr",
            comment=question.getFirstComment().getId(),
        )

        self.assertEqual(api.content.get_state(observation), "pending")
        self.assertEqual(api.content.get_state(question), "recalled-lr")
        helpers.login(self.portal, USERS.SE.value.name)
        self.assertIn(
            "Go to Conclusions",
            self.get_view(observation, ObservationView)(),
        )

    def test_lr_recall_restores_reopened_qa_state_after_observation_closed(self):
        helpers.login(self.portal, USERS.SE.value.name)
        observation = self.create_observation()
        question = self.create_question(observation, "question text")
        self.create_conclusion(observation, "draft conclusion text")
        api.content.transition(obj=observation, transition="reopen-qa-chat")

        helpers.login(self.portal, USERS.SE.value.name)
        api.content.transition(obj=observation, transition="draft-conclusions")
        api.content.transition(obj=observation, transition="finish-observation")

        helpers.login(self.portal, USERS.LR.value.name)
        api.content.transition(
            obj=observation, transition="confirm-finishing-observation"
        )
        observation.restrictedTraverse("recall-observation")()

        self.assertEqual(api.content.get_state(observation), "pending")
        self.assertEqual(api.content.get_state(question), "draft")
        self.assertEqual(
            api.content.get_state(observation.get_conclusion()),
            "draft",
        )
        helpers.login(self.portal, USERS.SE.value.name)
        self.assertIn(
            "Go to Conclusions",
            self.get_view(observation, ObservationView)(),
        )

    def test_draft_conclusion_hides_select_new_counterparts_action(self):
        helpers.login(self.portal, USERS.SE.value.name)
        observation = self.create_observation()
        self.create_conclusion(observation, "draft conclusion text")

        content = self.get_view(observation, ObservationView)()
        self.assertFalse("Select new Counterparts" in content)

    def test_conclusion_discussion_shows_select_new_counterparts_action(self):
        helpers.login(self.portal, USERS.SE.value.name)
        observation = self.create_observation()
        self.create_conclusion(observation, "draft conclusion text")
        api.content.transition(obj=observation, transition="request-comments")

        content = self.get_view(observation, ObservationView)()
        self.assertTrue("Select new Counterparts" in content)

    def test_closed_conclusion_comments_hide_select_new_counterparts_action(self):
        helpers.login(self.portal, USERS.SE.value.name)
        observation = self.create_observation()
        self.create_conclusion(observation, "draft conclusion text")
        api.content.transition(obj=observation, transition="request-comments")
        api.content.transition(obj=observation, transition="finish-comments")

        content = self.get_view(observation, ObservationView)()
        self.assertFalse("Select new Counterparts" in content)

    def test_assign_conclusion_reviewer_form_uses_reselect_transition(self):
        helpers.login(self.portal, USERS.SE.value.name)
        observation = self.create_observation()
        self.request.form["workflow_action"] = "reselect-counterparts"

        view = self.get_view(
            observation,
            AssignConclusionReviewerForm,
            name="assign_conclusion_reviewer_form",
        )
        self.assertEqual(view._get_wf_action(), "reselect-counterparts")

    def test_observation_actions_hide_workflow_follow_up_action(self):
        observation = self.create_observation()
        self.create_question(observation, "question text")
        view = self.get_view(observation, ObservationView)

        with patch(
            "emrt.necd.content.observation.getMenu",
            side_effect=[
                [
                    {
                        "action": (
                            "http://nohost/observation/edit-highlights"
                            "?_authenticator=test"
                        ),
                        "title": "Edit Key Flags",
                    }
                ],
                [
                    {
                        "action": (
                            "http://nohost/question/add-follow-up-question"
                            "?workflow_action=add-followup-question"
                            "&_authenticator=test"
                        ),
                        "title": "Add follow up question",
                    },
                    {
                        "action": (
                            "http://nohost/question/add-conclusions"
                            "?workflow_action=draft-conclusions"
                            "&_authenticator=test"
                        ),
                        "title": "Add Conclusions",
                    },
                    {
                        "action": (
                            "http://nohost/question/../add-conclusions"
                            "?workflow_action=draft-conclusions"
                            "&_authenticator=test"
                        ),
                        "title": "Go to Conclusions",
                    }
                ],
            ],
        ):
            actions = view.actions()

        self.assertEqual(
            [action["title"] for action in actions],
            ["Add Conclusions", "Go to Conclusions", "Edit Key Flags"],
        )

    def test_q_and_a_stage_defaults_to_questions_tab(self):
        observation = self.create_observation()
        view = self.get_view(observation, ObservationView)

        self.assertEqual(
            view.default_tab_selector(),
            'a[href="#tab-questions"]',
        )

    def test_conclusion_stage_defaults_to_conclusions_tab(self):
        helpers.login(self.portal, USERS.SE.value.name)
        observation = self.create_observation()
        self.create_conclusion(observation, "draft conclusion text")
        view = self.get_view(observation, ObservationView)

        self.assertEqual(
            view.default_tab_selector(),
            'a[href="#tab-conclusions"]',
        )

    def test_pending_observation_with_conclusion_keeps_q_and_a_tab_active(self):
        helpers.login(self.portal, USERS.SE.value.name)
        observation = self.create_observation()
        self.create_question(observation, "question text")
        self.create_conclusion(observation, "draft conclusion text")
        api.content.transition(obj=observation, transition="reopen-qa-chat")

        content = self.get_view(observation, ObservationView)()
        self.assertIn(
            '<div id="questionChatRoom" class="active"><a href="#tab-questions">Q&amp;A</a></div>',
            content,
        )
        self.assertNotIn(
            '<div class="active"><a href="#tab-conclusions">Conclusions</a></div>',
            content,
        )

    def test_end_review_blocks_answer_creation_for_msa(self):
        observation = self.create_observation()

        helpers.login(self.portal, USERS.SE.value.name)
        question = self.create_question(observation, "question text")
        api.content.transition(obj=question, transition="send-to-lr")

        helpers.login(self.portal, USERS.LR.value.name)
        question.getFirstComment().restrictedTraverse("approve-question")()
        setRoles(self.portal, USERS.LR.value.name, ["Manager"])
        api.content.transition(obj=self.tool, transition="end-review")

        helpers.login(self.portal, USERS.MSA.value.name)
        with self.assertRaises(Unauthorized):
            self.create_answer(question, text="The MSA answer")

    def test_end_review_blocks_question_recall_for_lr(self):
        observation = self.create_observation()

        helpers.login(self.portal, USERS.SE.value.name)
        question = self.create_question(observation, "question text")
        api.content.transition(obj=question, transition="send-to-lr")
        setRoles(self.portal, USERS.SE.value.name, ["Manager"])
        api.content.transition(obj=self.tool, transition="end-review")

        helpers.login(self.portal, USERS.LR.value.name)
        with self.assertRaises(api.exc.InvalidParameterError):
            api.content.transition(obj=question, transition="recall-question-lr")
