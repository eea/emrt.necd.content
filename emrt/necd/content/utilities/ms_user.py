from zope.interface import Interface
from zope.interface import implementer

import plone.api as api

from emrt.necd.content.constants import ROLE_MSA
from emrt.necd.content.constants import ROLE_MSE


class IUserIsMS(Interface):
    """ Returns True if the user has
        the MSAuthority or MSExpert roles.
    """


@implementer(IUserIsMS)
class UserIsMS(object):
    def __call__(self, context, user=None):
        user = user or api.user.get_current()
        roles = api.user.get_roles(user=user, obj=context)
        return ROLE_MSA in roles or ROLE_MSE in roles
