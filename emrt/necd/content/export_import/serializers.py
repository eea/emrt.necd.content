from zope.component import adapter

from plone.app.textfield.interfaces import IRichText
from plone.app.textfield import RichTextValue

from plone.restapi.serializer.converters import json_compatible

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