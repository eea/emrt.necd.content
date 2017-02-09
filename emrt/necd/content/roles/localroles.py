from Acquisition import aq_inner
from Acquisition import aq_parent
from borg.localrole.interfaces import ILocalRoleProvider
from emrt.necd.content.comment import IComment
from emrt.necd.content.commentanswer import ICommentAnswer
from emrt.necd.content.observation import IObservation
from emrt.necd.content.question import IQuestion
from emrt.necd.content.conclusionsphase2 import IConclusionsPhase2
from zope.component import adapts
from zope.interface import implements
from plone import api


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
        mtool = api.portal.get_tool('portal_membership')
        member = mtool.getMemberById(principal_id)
        roles = []
        if member is not None:
            context = aq_inner(self.context)
            country = context.country.lower()
            sector = context.ghg_source_category_value()
            groups = member.getGroups()
            if 'extranet-esd-esdreview-reviewexp-%s-%s' % (sector, country) in groups:
                roles.append('ReviewerPhase2')
            if 'extranet-esd-esdreview-leadreview-%s' % country in groups:
                roles.append('LeadReviewer')
            if 'extranet-esd-countries-msa-%s' % country in groups:
                roles.append('MSAuthority')
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
            mtool = api.portal.get_tool('portal_membership')
            member = mtool.getMemberById(principal_id)
            if member is not None:
                country = observation.country.lower()
                sector = observation.ghg_source_category_value()
                groups = member.getGroups()
                if 'extranet-esd-ghginv-qualityexpert-%s' % sector in groups:
                    roles.append('QualityExpert')
                if 'extranet-esd-esdreview-reviewexp-%s-%s' % (sector, country) in groups:
                    roles.append('ReviewerPhase2')
                if 'extranet-esd-esdreview-leadreview-%s' % country in groups:
                    roles.append('LeadReviewer')
                if 'extranet-esd-countries-msa-%s' % country in groups:
                    roles.append('MSAuthority')
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
                mtool = api.portal.get_tool('portal_membership')
                member = mtool.getMemberById(principal_id)
                if member is not None:
                    country = observation.country.lower()
                    sector = observation.ghg_source_category_value()
                    groups = member.getGroups()
                    if 'extranet-esd-ghginv-qualityexpert-%s' % sector in groups:
                        roles.append('QualityExpert')
                    if 'extranet-esd-esdreview-reviewexp-%s-%s' % (sector, country) in groups:
                        roles.append('ReviewerPhase2')
                    if 'extranet-esd-esdreview-leadreview-%s' % country in groups:
                        roles.append('LeadReviewer')
                    if 'extranet-esd-countries-msa-%s' % country in groups:
                        roles.append('MSAuthority')

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
                mtool = api.portal.get_tool('portal_membership')
                member = mtool.getMemberById(principal_id)
                if member is not None:
                    country = observation.country.lower()
                    sector = observation.ghg_source_category_value()
                    groups = member.getGroups()
                    if 'extranet-esd-ghginv-qualityexpert-%s' % sector in groups:
                        roles.append('QualityExpert')
                    if 'extranet-esd-esdreview-reviewexp-%s-%s' % (sector, country) in groups:
                        roles.append('ReviewerPhase2')
                    if 'extranet-esd-esdreview-leadreview-%s' % country in groups:
                        roles.append('LeadReviewer')
                    if 'extranet-esd-countries-msa-%s' % country in groups:
                        roles.append('MSAuthority')
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
            mtool = api.portal.get_tool('portal_membership')
            member = mtool.getMemberById(principal_id)
            if member is not None:
                country = observation.country.lower()
                sector = observation.ghg_source_category_value()
                groups = member.getGroups()
                if 'extranet-esd-ghginv-qualityexpert-%s' % sector in groups:
                    roles.append('QualityExpert')
                if 'extranet-esd-esdreview-reviewexp-%s-%s' % (sector, country) in groups:
                    roles.append('ReviewerPhase2')
                if 'extranet-esd-esdreview-leadreview-%s' % country in groups:
                    roles.append('LeadReviewer')
                if 'extranet-esd-countries-msa-%s' % country in groups:
                    roles.append('MSAuthority')
        if roles:
            from logging import getLogger
            log = getLogger(__name__)
            log.debug('Conclusions Phase 2 Roles: %s %s' % (principal_id, roles))

        return roles

    def getAllRoles(self):
        """Returns all the local roles assigned in this context:
        (principal_id, [role1, role2])"""
        return []
