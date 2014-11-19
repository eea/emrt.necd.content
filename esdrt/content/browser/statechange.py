from Acquisition import aq_inner
from Acquisition import aq_parent
from esdrt.content import MessageFactory as _
from plone import api
from plone.app.textfield import RichText
from plone.app.textfield.value import RichTextValue
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from z3c.form import button
from z3c.form import field
from z3c.form.form import Form
from zope import schema
from zope.interface import Interface
from esdrt.content.notifications.utils import notify
from Products.Five.browser.pagetemplatefile import PageTemplateFile


class IFinishObservationReasonForm(Interface):

    comments = RichText(
        title=_(u'Enter comments if you want'),
        required=False,
    )


class FinishObservationReasonForm(Form):
    fields = field.Fields(IFinishObservationReasonForm)
    label = _(u'Finish observation')
    description = _(u'Check the reason for requesting the closure of this observation')
    ignoreContext = True

    @button.buttonAndHandler(u'Finish observation')
    def finish_observation(self, action):
        comments = self.request.get('form.widgets.comments')
        with api.env.adopt_roles(['Manager']):
            if api.content.get_state(self.context) == 'phase1-conclusions':
                self.context.closing_comments = RichTextValue(comments, 'text/html', 'text/html')
                return self.context.content_status_modify(
                    workflow_action='phase1-request-close',
                )
            elif api.content.get_state(self.context) == 'phase2-conclusions':
                self.context.closing_comments_phase2 = RichTextValue(comments, 'text/html', 'text/html')
                return self.context.content_status_modify(
                    workflow_action='phase2-finish-observation',
                )

        self.request.response.redirect(self.context.absolute_url())

    def updateActions(self):
        super(FinishObservationReasonForm, self).updateActions()
        for k in self.actions.keys():
            self.actions[k].addClass('standardButton')


class IDenyFinishObservationReasonForm(Interface):

    comments = RichText(
        title=_(u'Enter your reasons to deny the finishing of this observation'),
        required=False,
    )


class DenyFinishObservationReasonForm(Form):
    fields = field.Fields(IDenyFinishObservationReasonForm)
    label = _(u'Deny finish observation')
    description = _(u'Check the reason for denying the finishing of this observation')
    ignoreContext = True

    @button.buttonAndHandler(u'Deny finishing observation')
    def finish_observation(self, action):
        comments = self.request.get('form.widgets.comments')
        with api.env.adopt_roles(['Manager']):
            if api.content.get_state(self.context) == 'phase1-close-requested':
                self.context.closing_deny_comments = RichTextValue(comments, 'text/html', 'text/html')
                return self.context.content_status_modify(
                    workflow_action='phase1-deny-closure',
                )
            elif api.content.get_state(self.context) == 'phase2-close-requested':
                self.context.closing_deny_comments_phase2 = RichTextValue(comments, 'text/html', 'text/html')
                return self.context.content_status_modify(
                    workflow_action='phase2-deny-finishing-observation',
                )

        return self.response.redirect(self.context.absolute_url())

    def updateActions(self):
        super(DenyFinishObservationReasonForm, self).updateActions()
        for k in self.actions.keys():
            self.actions[k].addClass('standardButton')


class IAssignAnswererForm(Interface):
    answerers = schema.Choice(
        title=_(u'Select the answerers'),
        vocabulary=u'plone.app.vocabularies.Users',
    )

    workflow_action = schema.TextLine(
        title=_(u'Workflow action'),
        required=True
    )


class AssignAnswererForm(BrowserView):

    index = ViewPageTemplateFile('templates/assign_answerer_form.pt')

    def revoke_all_roles(self):
        """
          Revoke all existing roles
        """
        target = self.assignation_target()
        for user, cp in self.get_counterpart_users():
            if cp:
                api.user.revoke_roles(username=user.getId(),
                    obj=target,
                    roles=['MSExpert'],
                )

    def assignation_target(self):
        return aq_parent(aq_inner(self.context))

    def target_groupname(self):
        context = aq_inner(self.context)
        observation = aq_parent(context)
        country = observation.country.lower()
        return 'extranet-esd-countries-msexpert-%s' % country

    def get_counterpart_users(self):
        groupname = self.target_groupname()
        current = api.user.get_current()
        current_id = current.getId()

        def isMSE(u):
            target = self.assignation_target()
            return 'MSExpert' in api.user.get_roles(user=u, obj=target)

        try:
            return [(u, isMSE(u)) for u in api.user.get_users(groupname=groupname) if current_id != u.getId()]
        except api.user.GroupNotFoundError:
            from logging import getLogger
            log = getLogger(__name__)
            log.info('There is not such a group %s' % groupname)
            return []

    def __call__(self):
        """Perform the update and redirect if necessary, or render the page
        """
        target = self.assignation_target()
        if self.request.form.get('send', None):
            usernames = self.request.get('counterparts', None)
            if not usernames:
                status = IStatusMessage(self.request)
                msg = _(u'You need to select at least one exper for discussion')
                status.addStatusMessage(msg, "error")
                return self.index()

            self.revoke_all_roles()

            for username in usernames:
                api.user.grant_roles(username=username,
                    roles=['MSExpert'],
                    obj=target)

            if api.content.get_state(self.context) in [u'phase1-pending', u'phase1-pending-answer-drafting']:
                wf_action = 'phase1-assign-answerer'
            elif api.content.get_state(self.context) in [u'phase2-pending', u'phase2-pending-answer-drafting']:
                wf_action = 'phase2-assign-answerer'
            else:
                status = IStatusMessage(self.request)
                msg = _(u'There was an error. Try again please')
                status.addStatusMessage(msg, "error")
                url = self.context.absolute_url()
                return self.request.response.redirect(url)

            return self.context.content_status_modify(
                workflow_action=wf_action,
            )

        else:
            self.revoke_all_roles()
            return self.index()

    def updateActions(self):
        super(AssignAnswererForm, self).updateActions()
        for k in self.actions.keys():
            self.actions[k].addClass('standardButton')


class IAssignCounterPartForm(Interface):
    counterpart = schema.TextLine(
        title=_(u'Select the counterpart'),
    )

    workflow_action = schema.TextLine(
        title=_(u'Workflow action'),
        required=True
    )


class AssignCounterPartForm(BrowserView):

    index = ViewPageTemplateFile('templates/assign_counterpart_form.pt')

    def revoke_all_roles(self):
        """
          Revoke all existing roles
        """
        target = self.assignation_target()
        for user, cp in self.get_counterpart_users():
            if cp:
                api.user.revoke_roles(username=user.getId(),
                    obj=target,
                    roles=['CounterPart'],
                )

    def target_groupnames(self):
        return [
            'extranet-esd-ghginv-sr',
            'extranet-esd-ghginv-qualityexpert',
            'extranet-esd-esdreview-reviewexp',
            'extranet-esd-esdreview-leadreview',
        ]

    def assignation_target(self):
        return aq_parent(aq_inner(self.context))

    def get_counterpart_users(self):
        current = api.user.get_current()
        current_id = current.getId()

        users = []

        def isCP(u):
            target = self.assignation_target()
            return 'CounterPart' in api.user.get_roles(user=u, obj=target)

        for groupname in self.target_groupnames():
            try:
                data = [(u, isCP(u)) for u in api.user.get_users(groupname=groupname) if current_id != u.getId()]
                users.extend(data)
            except api.user.GroupNotFoundError:
                from logging import getLogger
                log = getLogger(__name__)
                log.info('There is not such a group %s' % groupname)

        return users

    def __call__(self):
        """Perform the update and redirect if necessary, or render the page
        """
        target = self.assignation_target()
        if self.request.form.get('send', None):
            counterparts = self.request.get('counterparts', None)
            #comments = self.request.get('comments', None)
            if counterparts is None:
                status = IStatusMessage(self.request)
                msg = _(u'You need to select at least one counterpart')
                status.addStatusMessage(msg, "error")
                return self.index()

            self.revoke_all_roles()

            for username in counterparts:
                api.user.grant_roles(username=username,
                    roles=['CounterPart'],
                    obj=target)

            if api.content.get_state(self.context) == 'phase1-draft':
                wf_action = 'phase1-request-for-counterpart-comments'
            elif api.content.get_state(self.context) == 'phase2-draft':
                wf_action = 'phase2-request-for-counterpart-comments'
            else:
                status = IStatusMessage(self.request)
                msg = _(u'There was an error. Try again please')
                status.addStatusMessage(msg, "error")
                url = self.context.absolute_url()
                return self.request.response.redirect(url)

            return self.context.content_status_modify(
                workflow_action=wf_action,

            )

        else:
            self.revoke_all_roles()
            return self.index()

    def updateActions(self):
        super(AssignCounterPartForm, self).updateActions()
        for k in self.actions.keys():
            self.actions[k].addClass('standardButton')


class IAssignConclusionReviewerForm(Interface):
    reviewers = schema.Choice(
        title=_(u'Select the conclusion reviewers'),
        vocabulary=u'plone.app.vocabularies.Users',
    )


class ReAssignCounterPartForm(AssignCounterPartForm):

    index = ViewPageTemplateFile('templates/assign_counterpart_form.pt')

    def __call__(self):
        """Perform the update and redirect if necessary, or render the page
        """
        target = self.assignation_target()
        if self.request.form.get('send', None):
            counterparts = self.request.get('counterparts', None)
            #comments = self.request.get('comments', None)
            if counterparts is None:
                status = IStatusMessage(self.request)
                msg = _(u'You need to select at least one counterpart')
                status.addStatusMessage(msg, "error")
                return self.index()

            self.revoke_all_roles()

            for username in counterparts:
                api.user.grant_roles(username=username,
                    roles=['CounterPart'],
                    obj=target)

            status = IStatusMessage(self.request)
            msg = _(u'CounterParts reassigned correctly')
            status.addStatusMessage(msg, "info")
            url = self.context.absolute_url()

            subject = u'New draft question to comment'
            _temp = PageTemplateFile('../notifications/question_to_counterpart.pt')
            notify(target, _temp, subject, roles=['CounterPart'])


            return self.request.response.redirect(url)

        else:
            return self.index()


class AssignConclusionReviewerForm(BrowserView):

    index = ViewPageTemplateFile('templates/assign_conclusion_reviewer_form.pt')

    def update(self):
        self.revoke_all_roles()

    def revoke_all_roles(self):
        """
          Revoke all existing roles
        """
        target = self.assignation_target()
        for user, cp in self.get_counterpart_users():
            if cp:
                api.user.revoke_roles(username=user.getId(),
                    obj=target,
                    roles=['CounterPart'],
                )

    def assignation_target(self):
        return aq_parent(aq_inner(self.context))

    def target_groupnames(self):
        return [
            'extranet-esd-ghginv-sr',
            'extranet-esd-ghginv-qualityexpert',
            'extranet-esd-esdreview-reviewexp',
            'extranet-esd-esdreview-leadreview',
        ]

    def get_counterpart_users(self):
        current = api.user.get_current()
        current_id = current.getId()

        users = []

        def isCP(u):
            target = self.assignation_target()
            return 'CounterPart' in api.user.get_roles(user=u, obj=target)

        for groupname in self.target_groupnames():
            try:
                data = [(u, isCP(u)) for u in api.user.get_users(groupname=groupname) if current_id != u.getId()]
                users.extend(data)
            except api.user.GroupNotFoundError:
                from logging import getLogger
                log = getLogger(__name__)
                log.info('There is not such a group %s' % groupname)

        return users

    def __call__(self):
        """Perform the update and redirect if necessary, or render the page
        """
        target = self.assignation_target()
        if self.request.form.get('send', None):
            usernames = self.request.form.get('counterparts', None)
            if not usernames:
                status = IStatusMessage(self.request)
                msg = _(u'You need to select at least one reviewer for conclusions')
                status.addStatusMessage(msg, "error")
                return self.index()

            self.revoke_all_roles()

            for username in usernames:
                api.user.grant_roles(username=username,
                    obj=target,
                    roles=['CounterPart'],
                )

            if api.content.get_state(self.context).startswith('phase1-'):
                wf_action = 'phase1-request-comments'
            elif api.content.get_state(self.context).startswith('phase2-'):
                wf_action = 'phase2-request-comments'
            else:
                status = IStatusMessage(self.request)
                msg = _(u'There was an error. Try again please')
                status.addStatusMessage(msg, "error")
                url = self.context.absolute_url()
                return self.request.response.redirect(url)

            return self.context.content_status_modify(
                workflow_action=wf_action,
            )

        else:
            return self.index()

    def updateActions(self):
        super(AssignConclusionReviewerForm, self).updateActions()
        for k in self.actions.keys():
            self.actions[k].addClass('standardButton')
