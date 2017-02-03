from zope.annotation.interfaces import IAnnotations
from BTrees.OOBTree import OOBTree


# SUBSCRIPTION_KEY = 'emrt.necd.content.subscriptions.subscribed'
UNSUBSCRIPTION_KEY = 'emrt.necd.content.subscriptions.unsubscribed'


# class NotificationSubscriptions(object):

#     def __init__(self, context):
#         self.context = context

#     def get(self):
#         annotated = IAnnotations(self.context)
#         return list(annotated.get(SUBSCRIPTION_KEY, OOBTree()))

#     def add_notifications(self, userid):
#         annotated = IAnnotations(self.context)
#         data = annotated.get(SUBSCRIPTION_KEY, OOBTree())
#         if data.add(userid):
#             annotated[SUBSCRIPTION_KEY] = data
#             return 1
#         return 0

#     def del_notifications(self, userid):
#         annotated = IAnnotations(self.context)
#         data = annotated.get(SUBSCRIPTION_KEY, OOBTree())
#         try:
#             data.remove(userid)
#             annotated[SUBSCRIPTION_KEY] = data
#             return 1
#         except KeyError:
#             return 0

#         return 0


class NotificationUnsubscriptions(object):

    def __init__(self, context):
        self.context = context

    def get(self):
        annotated = IAnnotations(self.context)
        return annotated.get(UNSUBSCRIPTION_KEY, OOBTree())

    def get_user_data(self, userid):
        return self.get().get(userid, OOBTree())

    def unsubscribe(self, userid, notifications={}, roles=[]):
        """
        Save the unsubscribed notifications dict.
        The key of the dict should be the role name, and the value
         the list of notifications that will be unsubscribed:

         {
            'CounterPart': ['conclusion_to_comment'],
            'ReviewerPhase1': ['observation_finalised', 'question_to_ms'],
         }
        """
        annotated = IAnnotations(self.context)
        data = annotated.get(UNSUBSCRIPTION_KEY, OOBTree())
        if notifications:
            data[userid] = notifications
        else:
            del data[userid]
        annotated[UNSUBSCRIPTION_KEY] = data
        return 1

