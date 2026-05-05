from plone.app.textfield import RichTextValue
from z3c.form.action import Actions
from z3c.form.field import FieldWidgets

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from emrt.necd.content.review_state import reviewfolder_allows_mutation
from plone.app.discussion.browser.comments import CommentForm as BaseForm
from plone.app.discussion.browser.comments import (
    CommentsViewlet as BaseViewlet,
)


class CommentForm(BaseForm):
    widgets: FieldWidgets
    actions: Actions

    def updateWidgets(self):
        super(CommentForm, self).updateWidgets()
        self.widgets["text"].rows = 15

    def updateActions(self):
        super(CommentForm, self).updateActions()
        self.actions["comment"].title = "Save Comment"
        for k in list(self.actions.keys()):
            self.actions[k].addClass("standardButton")
            self.actions[k].addClass("defaultWFButton")


class CommentsViewlet(BaseViewlet):
    index = ViewPageTemplateFile("./templates/comments.pt")
    form = CommentForm

    def can_reply(self):
        return reviewfolder_allows_mutation(self.context) and super(
            CommentsViewlet, self
        ).can_reply()

    def render_rich_text_reply(self, reply):
        if isinstance(reply.text, RichTextValue):
            return reply.text.output_relative_to(self.context)
        else:
            return reply.getText()
