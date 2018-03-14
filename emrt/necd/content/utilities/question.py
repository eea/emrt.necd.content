from AccessControl import getSecurityManager


class FollowUpPermission(object):

    def __call__(self, question):
        if question:
            sm = getSecurityManager()
            permission = sm.checkPermission('emrt.necd.content: Add Comment',
                                            question)
            questions = [q for q in question.values()
                         if q.portal_type == 'Comment']
            answers = [q for q in question.values()
                       if q.portal_type == 'CommentAnswer']
            return permission and len(questions) == len(answers)

        else:
            return False

