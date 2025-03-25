from zope.component import adapter
from zope.interface import implementer

from plone.theme.interfaces import IDefaultPloneLayer

from plone.app.textfield.interfaces import IRichText
from plone.app.textfield import RichTextValue

from plone.app.discussion.interfaces import IComment as IDiscussionComment

from plone.restapi.serializer.converters import json_compatible
from plone.restapi.serializer.discussion import CommentSerializer

from plone.restapi.interfaces import ISerializeToJson

from collective.exportimport.interfaces import IRawRichTextMarker
from collective.exportimport.serializer import RichttextFieldSerializerWithRawText

from emrt.necd.content.comment import IComment
from emrt.necd.content.commentanswer import ICommentAnswer


class NECDRichTextFieldSerializer(RichttextFieldSerializerWithRawText):
    def __call__(self):
        value = self.get_value()
        if isinstance(value, RichTextValue):
            return super(NECDRichTextFieldSerializer, self).__call__()
        elif value:
            return {
                u"data": json_compatible(u"<p>{}</p>".format(value)),
                u"content-type": json_compatible("text/html"),
                u"encoding": json_compatible("utf-8"),
            }


@adapter(IRichText, IComment, IRawRichTextMarker)
class CommentTextSerializer(NECDRichTextFieldSerializer):
    """ Serializer for Comment text """


@adapter(IRichText, ICommentAnswer, IRawRichTextMarker)
class CommentAnswerTextSerializer(NECDRichTextFieldSerializer):
    """ Serializer for CommentAnswer text """


@implementer(ISerializeToJson)
@adapter(IDiscussionComment, IDefaultPloneLayer)
class DiscussionCommentSerializer(CommentSerializer):
    def __call__(self, include_items=True):
        result = super(DiscussionCommentSerializer, self).__call__(include_items)
        if isinstance(result["text"]["data"], RichTextValue):
            result["text"]["data"] = result["text"]["data"].raw
            result["text"]["mime-type"] = u"text/html"
        return result
