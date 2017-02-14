from Acquisition import aq_inner
from Acquisition import aq_parent
from plone.app.discussion.interfaces import IComment
from five import grok


class CopyFileToAnswer(grok.View):
    grok.require('emrt.necd.content.AddNECDFile')
    grok.context(IComment)
    grok.name('copy-attachment-to-answer')

    def render(self):
        context = aq_inner(self.context)
        conversation = aq_parent(context)
        answer = aq_parent(conversation)
        file = getattr(context, 'attachment', None)
        candidate_id = file.filename
        while candidate_id in answer.keys():
            candidate_id += '-1'

        filename = answer.invokeFactory(
            id=candidate_id,
            type_name='NECDFile',
            file=file,
        )
        return self.request.response.redirect(context.absolute_url())
