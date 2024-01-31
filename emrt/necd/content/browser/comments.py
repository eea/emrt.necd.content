from z3c.form import button

from plone.app.textfield.interfaces import IRichTextValue
from plone.app.discussion.browser.comments import CommentForm as BaseForm
from plone.app.discussion.interfaces import IConversation

from emrt.necd.theme.browser.viewlets import NECDCommentsViewlet
from emrt.necd.content import MessageFactory as _


class CommentForm(BaseForm):

    _text_value = None

    def extractData(self, setErrors=True):
        """
        Extract RichTextValue to be saved after it's parent is committed.

        This is a work-around for InvalidObjectReference since RichTextValue
        is not persistent itself, but RawValueHolder is.

        As the form is saved in a Comment which has a Conversation parent and
        during the normal creation process we have a parent object without an
        oid, which has a non-persistent object which has a persistent object
        without an oid.
        """
        data, errors = super(CommentForm, self).extractData(setErrors)
        text = data.get("text", "")

        if IRichTextValue.providedBy(text):
            self._text_value = text
            data["text"] = ""

        return data, errors

    def updateWidgets(self):
        super(CommentForm, self).updateWidgets()
        self.widgets['text'].rows = 15

    def updateActions(self):
        super(CommentForm, self).updateActions()
        self.actions['comment'].title = u'Save Comment'
        for k in self.actions.keys():
            self.actions[k].addClass('standardButton')
            self.actions[k].addClass('defaultWFButton')


    @button.buttonAndHandler(_(u"add_comment_button", default=u"Comment"),
                             name='comment')
    def handleComment(self, action):
        super(CommentForm, self).handleComment.func(self, action)

        if self._text_value is not None:
            conversation = IConversation(self.__parent__)
            added_comment = conversation.get(conversation.keys()[-1])
            added_comment.text = self._text_value

    @button.buttonAndHandler(_(u"Cancel"))
    def handleCancel(self, action):
        super(CommentForm, self).handleCancel(action)


class CommentsViewlet(NECDCommentsViewlet):
    form = CommentForm
