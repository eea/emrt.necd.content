from Acquisition import aq_inner
from Acquisition import aq_parent
from borg.localrole.interfaces import ILocalRoleProvider
from zope.component import adapts
from zope.interface import implements

import plone.api as api

from emrt.necd.content.comment import IComment
from emrt.necd.content.commentanswer import ICommentAnswer
from emrt.necd.content.observation import IObservation
from emrt.necd.content.question import IQuestion
from emrt.necd.content.conclusionsphase2 import IConclusionsPhase2
from emrt.necd.content.constants import LDAP_SECTOREXP
from emrt.necd.content.constants import LDAP_LEADREVIEW
from emrt.necd.content.constants import LDAP_MSA


def get_user_roles_in_context(context, principal_id):
    mtool = api.portal.get_tool('portal_membership')
    member = mtool.getMemberById(principal_id)
    roles = []
    if member is not None:
        context = aq_inner(context)
        country = context.country.lower()
        sector = context.ghg_source_category_value()
        groups = member.getGroups()
        if '{}-{}-{}'.format(LDAP_SECTOREXP, sector, country) in groups:
            roles.append('ReviewerPhase2')
        if '{}-{}'.format(LDAP_LEADREVIEW, country) in groups:
            roles.append('LeadReviewer')
        if '{}-{}'.format(LDAP_MSA, country) in groups:
            roles.append('MSAuthority')
    return roles


class ObservationRoleAdapter(object):
    implements(ILocalRoleProvider)
    adapts(IObservation)

    def __init__(self, context):
        self.context = context

    def getRoles(self, principal_id):
        """Returns the roles for the given principal in context.

        This function is additional besides other ILocalRoleProvider plug-ins.

        @param context: Any Plone object
        @param principal_id: User login id
        """
        roles = get_user_roles_in_context(self.context, principal_id)
        if roles:
            from logging import getLogger
            log = getLogger(__name__)
            log.debug('Observation Roles: %s %s' % (principal_id, roles))

        return roles

    def getAllRoles(self):
        """Returns all the local roles assigned in this context:
        (principal_id, [role1, role2])"""
        return []


class QuestionRoleAdapter(object):
    implements(ILocalRoleProvider)
    adapts(IQuestion)

    def __init__(self, context):
        self.context = context

    def getRoles(self, principal_id):
        """Returns the roles for the given principal in context.

        This function is additional besides other ILocalRoleProvider plug-ins.

        @param context: Any Plone object
        @param principal_id: User login id
        """
        observation = aq_parent(aq_inner(self.context))
        roles = []
        if IObservation.providedBy(observation):
            roles = get_user_roles_in_context(observation, principal_id)
        if roles:
            from logging import getLogger
            log = getLogger(__name__)
            log.debug('Question Roles: %s %s' % (principal_id, roles))

        return roles

    def getAllRoles(self):
        """Returns all the local roles assigned in this context:
        (principal_id, [role1, role2])"""
        return []


class CommentRoleAdapter(object):
    implements(ILocalRoleProvider)
    adapts(IComment)

    def __init__(self, context):
        self.context = context

    def getRoles(self, principal_id):
        """Returns the roles for the given principal in context.

        This function is additional besides other ILocalRoleProvider plug-ins.

        @param context: Any Plone object
        @param principal_id: User login id
        """
        comment = aq_inner(self.context)
        question = aq_parent(comment)
        roles = []
        if IQuestion.providedBy(question):
            observation = aq_parent(question)
            if IObservation.providedBy(observation):
                roles = get_user_roles_in_context(observation, principal_id)
        if roles:
            from logging import getLogger
            log = getLogger(__name__)
            log.debug('Comment Roles: %s %s' % (principal_id, roles))

        return roles

    def getAllRoles(self):
        """Returns all the local roles assigned in this context:
        (principal_id, [role1, role2])"""
        return []


class CommentAnswerRoleAdapter(object):
    implements(ILocalRoleProvider)
    adapts(ICommentAnswer)

    def __init__(self, context):
        self.context = context

    def getRoles(self, principal_id):
        """Returns the roles for the given principal in context.

        This function is additional besides other ILocalRoleProvider plug-ins.

        @param context: Any Plone object
        @param principal_id: User login id
        """
        commentanswer = aq_inner(self.context)
        question = aq_parent(commentanswer)
        roles = []
        if IQuestion.providedBy(question):
            observation = aq_parent(question)
            if IObservation.providedBy(observation):
                roles = get_user_roles_in_context(observation, principal_id)
        if roles:
            from logging import getLogger
            log = getLogger(__name__)
            log.debug('CommentAnswer Roles: %s %s' % (principal_id, roles))

        return roles

    def getAllRoles(self):
        """Returns all the local roles assigned in this context:
        (principal_id, [role1, role2])"""
        return []


class ConclusionPhase2RoleAdapter(object):
    implements(ILocalRoleProvider)
    adapts(IConclusionsPhase2)

    def __init__(self, context):
        self.context = context

    def getRoles(self, principal_id):
        """Returns the roles for the given principal in context.

        This function is additional besides other ILocalRoleProvider plug-ins.

        @param context: Any Plone object
        @param principal_id: User login id
        """
        observation = aq_parent(aq_inner(self.context))
        roles = []
        if IObservation.providedBy(observation):
            roles = get_user_roles_in_context(observation, principal_id)
        if roles:
            from logging import getLogger
            log = getLogger(__name__)
            log.debug('Conclusions Phase 2 Roles: %s %s' % (principal_id, roles))

        return roles

    def getAllRoles(self):
        """Returns all the local roles assigned in this context:
        (principal_id, [role1, role2])"""
        return []