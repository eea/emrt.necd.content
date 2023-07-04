"""Documentation:
-   https://github.com/tisto/collective.ploneboard/blob/master/src/collective/ploneboard/browser/commentextender.py
-   http://plone.293351.n2.nabble.com/GSoC-2014-Collective-Ploneboard-Attachment-issue-tp7571746p7571837.html.
"""
from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from persistent import Persistent
from z3c.form import interfaces
from z3c.form.datamanager import AttributeField
from z3c.form.field import Fields
from z3c.form.interfaces import IDataManager

from Acquisition import Implicit
from zope import schema
from zope.annotation import factory
from zope.component import adapter
from zope.interface import Interface
from zope.interface import implementer
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.schema.interfaces import IList

from Products.CMFCore import permissions

from plone.app.discussion.browser.comments import CommentForm
from plone.app.discussion.comment import IComment
from plone.formwidget.multifile import MultiFileFieldWidget
from plone.namedfile.field import NamedBlobFile
from plone.z3cform.fieldsets import extensible

from emrt.necd.content import MessageFactory as _
from emrt.necd.content.comment import IComment as ICommentContent
from emrt.necd.content.constants import P_OBS_REDRAFT_REASON_VIEW


class IMultiFileField(IList):
    """IMultiFileField."""


@implementer(IMultiFileField)
class MultiFileField(schema.List):
    """MultiFileField."""


@implementer(IDataManager)
@adapter(ICommentContent, IMultiFileField)
class MultiFileFieldDataManager(AttributeField):
    """MultiFileField data manager."""

    @property
    def adapted_context(self):
        try:
            return super().adapted_context
        except TypeError:
            return self.context

    def query(self, default=None):
        return super().query(default=default)


class ICommentExtenderFields(Interface):
    attachment = NamedBlobFile(
        title=_("Attachment"),
        description=_(""),
        required=False,
    )

    attachments = MultiFileField(
        title="Attachments",
        value_type=NamedBlobFile(),
        required=False,
    )

    redraft_message = schema.Text(
        title=_("Redraft reason"),
        required=False,
    )

    redraft_date = schema.Datetime(
        title=_("Redraft request date"),
        required=False,
    )


@implementer(ICommentExtenderFields)
@adapter(IComment)
class CommentExtenderFields(Implicit, Persistent):
    security = ClassSecurityInfo()

    security.declareProtected(permissions.View, "attachment")
    attachment = None
    attachments = None

    security.declareProtected(P_OBS_REDRAFT_REASON_VIEW, "redraft_message")
    redraft_message = ""

    redraft_date = None


InitializeClass(CommentExtenderFields)

CommentExtenderFactory = factory(CommentExtenderFields)


@adapter(Interface, IDefaultBrowserLayer, CommentForm)
class CommentExtender(extensible.FormExtender):
    fields = Fields(ICommentExtenderFields)

    def __init__(self, context, request, form):
        self.context = context
        self.request = request
        self.form = form

    def update(self):
        self.add(ICommentExtenderFields, prefix="")
        self.move("attachment", after="text", prefix="")
        self.form.description = _(
            "Handling of confidential files: "
            "Please zip your file, protect it with a password, upload it to your reply in the EEA review tool "
            "and send the password per email to the EMRT-NECD Secretariat mailbox. "
            "Your password will only be shared with the lead reviewer and sector Expert. "
        )
        self.form.fields["redraft_message"].mode = interfaces.HIDDEN_MODE
        self.form.fields["redraft_date"].mode = interfaces.HIDDEN_MODE
        # self.form.fields["attachment"].mode = interfaces.HIDDEN_MODE
        # TODO: make this work
        self.form.fields["attachments"].widgetFactory = MultiFileFieldWidget
