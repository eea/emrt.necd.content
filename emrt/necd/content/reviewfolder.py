import time
import tablib
from datetime import datetime
from Acquisition import aq_inner
from AccessControl import getSecurityManager, Unauthorized
from five import grok
from plone import api
from plone.app.content.browser.tableview import Table
from plone.batching import Batch
from plone.directives import dexterity
from plone.directives import form
from plone.memoize import ram
from plone.memoize.view import memoize
from plone.namedfile.interfaces import IImageScaleTraversable
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from emrt.necd.content.timeit import timeit
from eea.cache import cache
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.interfaces import IContextSourceBinder
from zc.dict import OrderedDict
from z3c.form import button
from z3c.form import field
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema import List, Choice, TextLine
from zope.interface import Interface
from zope.interface import provider
from z3c.form.interfaces import HIDDEN_MODE
from emrt.necd.content.utilities.ms_user import IUserIsMS
from emrt.necd.content.constants import LDAP_LEADREVIEW
from emrt.necd.content.constants import LDAP_SECTOREXP
from emrt.necd.content.constants import LDAP_MSEXPERT
from emrt.necd.content.constants import LDAP_MSA

grok.templatedir('templates')


# Cache helper methods
def _user_name(fun, self, userid):
    return (userid, time.time() // 86400)


class IReviewFolder(form.Schema, IImageScaleTraversable):
    """
    Folder to have all observations together
    """


class ReviewFolder(dexterity.Container):
    grok.implements(IReviewFolder)


class ReviewFolderMixin(grok.View):
    grok.baseclass()

    @memoize
    def get_questions(self, sort_on="modified", sort_order="reverse"):
        country = self.request.form.get('country', '')
        reviewYear = self.request.form.get('reviewYear', '')
        inventoryYear = self.request.form.get('inventoryYear', '')
        status = self.request.form.get('status', '')
        highlights = self.request.form.get('highlights', '')
        freeText = self.request.form.get('freeText', '')
        step = self.request.form.get('step', '')
        wfStatus = self.request.form.get('wfStatus', '')
        nfrCode = self.request.form.get('nfrCode', '')

        catalog = api.portal.get_tool('portal_catalog')
        path = '/'.join(self.context.getPhysicalPath())
        query = {
            'path': path,
            'portal_type': ['Observation'],
            'sort_on': sort_on,
            'sort_order': sort_order
        }

        if self.is_member_state_coordinator():
            query['observation_sent_to_msc'] = bool(True)

        if self.is_member_state_expert():
            query['observation_sent_to_mse'] = bool(True)

        if (country != ""):
            query['Country'] = country
        if (status != ""):
            if status != "open":
                query['observation_finalisation_reason'] = status
            else:
                query['review_state'] = [
                    'phase2-pending',
                    'phase2-close-requested',
                    'phase2-draft',
                    'phase2-conclusions',
                    'phase2-conclusion-discussion',
                ]

        if reviewYear != "":
            query['review_year'] = reviewYear
        if inventoryYear != "":
            query['year'] = inventoryYear
        if highlights != "":
            query['highlight'] = highlights.split(",")
        if freeText != "":
            query['SearchableText'] = freeText
        if step != "":
            query['observation_step'] = step
        if wfStatus != "":
            query['observation_status'] = wfStatus
        if nfrCode != "":
            query['nfr_code'] = nfrCode

        return catalog(query)

    def can_add_observation(self):
        sm = getSecurityManager()
        return sm.checkPermission('emrt.necd.content: Add Observation', self)

    def is_secretariat(self):
        user = api.user.get_current()
        return 'Manager' in user.getRoles()

    def get_countries(self):
        vtool = getToolByName(self, 'portal_vocabularies')
        voc = vtool.getVocabularyByName('eea_member_states')
        countries = []
        voc_terms = voc.getDisplayList(self).items()
        for term in voc_terms:
            countries.append((term[0], term[1]))

        return countries

    def get_highlights(self):
        vtool = getToolByName(self, 'portal_vocabularies')
        voc = vtool.getVocabularyByName('highlight')
        highlights = []
        voc_terms = voc.getDisplayList(self).items()
        for term in voc_terms:
            highlights.append((term[0], term[1]))

        return highlights

    def get_review_years(self):
        catalog = api.portal.get_tool('portal_catalog')
        review_years = catalog.uniqueValuesFor('review_year')
        review_years = [c for c in catalog.uniqueValuesFor('review_year') if isinstance(c, basestring)]
        return review_years

    def get_inventory_years(self):
        catalog = api.portal.get_tool('portal_catalog')
        inventory_years = catalog.uniqueValuesFor('year')
        return inventory_years

    def get_nfr_categories(self):
        vocab_factory = getUtility(
            IVocabularyFactory, name='emrt.necd.content.nfr_code')
        vocabulary = vocab_factory(self.context)
        return [(x.value, x.title) for x in vocabulary]

    def get_finalisation_reasons(self):
        vtool = getToolByName(self, 'portal_vocabularies')
        reasons = [('open', 'open')]
        if self.context.Title() == '2015':
            voc = vtool.getVocabularyByName('conclusion_phase2_reasons')
            voc_terms = voc.getDisplayList(self).items()
            for term in voc_terms:
                if "2016" not in term[0]:
                    reasons.append((term[0], term[1]))
            return reasons
        else:
            voc = vtool.getVocabularyByName('conclusion_phase2_reasons')
            voc_terms = voc.getDisplayList(self).items()
            for term in voc_terms:
                if "2016" in term[0]:
                    reasons.append((term[0], term[1]))
            return reasons

    def is_member_state_coordinator(self):
        if api.user.is_anonymous():
            raise Unauthorized
        user = api.user.get_current()
        return LDAP_MSA in user.getGroups()

    def is_member_state_expert(self):
        user = api.user.get_current()
        return LDAP_MSEXPERT in user.getGroups()


class ReviewFolderView(ReviewFolderMixin):
    grok.context(IReviewFolder)
    grok.require('zope2.View')
    grok.name('view')

    def contents_table(self):
        table = ReviewFolderBrowserView(aq_inner(self.context), self.request)
        return table.render()

    def can_export_observations(self):
        sm = getSecurityManager()
        return sm.checkPermission('emrt.necd.content: Export Observations', self)


class ReviewFolderBrowserView(ReviewFolderMixin):
    grok.context(IReviewFolder)
    grok.require('zope2.View')
    grok.name('get_table')

    def folderitems(self, sort_on="modified", sort_order="reverse"):
        """
        """

        questions = self.get_questions(sort_on, sort_order)
        results = []
        for i, obj in enumerate(questions):
            results.append(dict(
                brain=obj
            ))

        return results

    def table(self, context, request, sort_on='modified', sort_order="reverse"):
        pagesize = int(self.request.get('pagesize', 20))
        url = context.absolute_url()
        view_url = url + '/view'

        table = Table(
            self.request, url, view_url, self.folderitems(sort_on, sort_order),
            pagesize=pagesize
        )

        table.render = ViewPageTemplateFile("templates/reviewfolder_get_table.pt")
        table.is_secretariat = self.is_secretariat

        return table

    def update_table(self, pagenumber='1', sort_on='modified',
                     sort_order="reverse", show_all=False):
        self.request.set('sort_on', sort_on)
        self.request.set('pagenumber', pagenumber)

        table = self.table(
            self.context, self.request, sort_on=sort_on, sort_order=sort_order
        )

        return table.render(table)

    def render(self):
        sort_on = self.request.get('sort_on', 'modified')
        sort_order = self.request.get('sort_order', 'reverse')
        pagenumber = self.request.get('pagenumber', '1')
        return self.update_table(pagenumber, sort_on, sort_order)


EXPORT_FIELDS = OrderedDict([
    ('getURL', 'URL'),
    ('get_ghg_source_sectors', 'Sector'),
    ('country_value', 'Country'),
    ('text', 'Detail'),
    ('observation_is_potential_significant_issue', 'Is potential significant issue'),
    ('observation_is_potential_technical_correction', 'Is potential technical correction'),
    ('observation_is_technical_correction', 'Is technical correction'),
    ('nfr_code_value', 'NFR Code'),
    ('review_year', 'Review Year'),
    ('year', 'Inventory year'),
    ('pollutants_value', 'Pollutants'),
    ('get_highlight', 'Highlight'),
    ('overview_status', 'Status'),
    ('observation_phase', 'Step'),
    ('observation_finalisation_reason_step2', 'Conclusion step 2'),
    ('observation_finalisation_text_step2', 'Conclusion step 2 note'),
    ('observation_status', 'Workflow'),
    ('get_author_name', 'Author')
])

# Don't show conclusion notes to MS users.
EXCLUDE_FIELDS_FOR_MS = (
    'observation_finalisation_text_step2',
)


@provider(IContextSourceBinder)
def fields_vocabulary_factory(context):
    terms = []
    user_is_ms = getUtility(IUserIsMS)(context)
    for key, value in EXPORT_FIELDS.items():
        if user_is_ms and key in EXCLUDE_FIELDS_FOR_MS:
            continue
        terms.append(SimpleVocabulary.createTerm(key, key, value))
    return SimpleVocabulary(terms)


class IExportForm(Interface):
    exportFields = List(
        title=u"Fields to export",
        description=u"Select which fields you want to add into XLS",
        required=False,
        value_type=Choice(source=fields_vocabulary_factory)
    )

    come_from = TextLine(title=u"Come from")


class ExportReviewFolderForm(form.Form, ReviewFolderMixin):
    grok.context(IReviewFolder)
    grok.require('emrt.necd.content.ExportObservations')
    grok.name('export_as_xls')

    fields = field.Fields(IExportForm)
    ignoreContext = True

    label = u"Export observations in XLS format"
    name = u"export-observation-form"

    def updateWidgets(self):
        super(ExportReviewFolderForm, self).updateWidgets()
        self.widgets['exportFields'].size = 20
        self.widgets['come_from'].mode = HIDDEN_MODE
        self.widgets['come_from'].value = '%s?%s' % (
            self.context.absolute_url(), self.request['QUERY_STRING']
        )

    def action(self):
        return '%s/export_as_xls?%s' % (
            self.context.absolute_url(),
            self.request['QUERY_STRING']
        )

    @button.buttonAndHandler(u'Export')
    def handleExport(self, action):
        data, errors = self.extractData()

        if errors:
            self.status = self.formErrorsMessage
            return

        return self.build_file(data)

    @button.buttonAndHandler(u"Back")
    def handleCancel(self, action):
        return self.request.response.redirect(
            '%s?%s' % (self.context.absolute_url(), self.request['QUERY_STRING'])
        )

    def updateActions(self):
        super(ExportReviewFolderForm, self).updateActions()
        for k in self.actions.keys():
            self.actions[k].addClass('standardButton')

    def render(self):
        if not self.request.get('form.buttons.extend', None):
            return super(ExportReviewFolderForm, self).render()

    def translate_highlights(self, highlights):
        return [
            self._vocabulary_value(
                'emrt.necd.content.highlight',
                highlight
            ) for highlight in highlights
        ]

    def _vocabulary_value(self, vocabulary, term):
        vocab_factory = getUtility(IVocabularyFactory, name=vocabulary)
        vocabulary = vocab_factory(self)
        if not term:
            return u''
        try:
            value = vocabulary.getTerm(term)
            return value.title
        except LookupError:
            return term

    def extract_data(self, data):
        """ Create xls file
        """
        observations = self.get_questions()

        user_is_ms = getUtility(IUserIsMS)(self.context)

        fields_to_export = [
            name for name in data.get('exportFields', []) if
            not user_is_ms or name not in EXCLUDE_FIELDS_FOR_MS
        ]
        data = tablib.Dataset()
        data.title = "Observations"
        for observation in observations:
            row = [observation.getId]
            for key in fields_to_export:
                if key in [
                    'observation_is_potential_significant_issue',
                    'observation_is_potential_technical_correction',
                    'observation_is_technical_correction'
                ]:
                    row.append(observation[key] and 'Yes' or 'No')
                elif key=='getURL':
                    row.append(observation.getURL())
                elif key=='get_highlight':
                    row.append(
                        safe_unicode(', '.join(
                            self.translate_highlights(observation[key] or [])
                        ))
                    )
                elif key=='overview_status':
                    row.append(
                        safe_unicode(
                            observation[key].replace('<br>', '').replace('<br/>', '')
                        ),
                    )
                else:
                    row.append(safe_unicode(observation[key]))
            data.append(row)

        headers = ['Observation']
        headers.extend([EXPORT_FIELDS[k] for k in fields_to_export])
        data.headers = headers
        return data

    def build_file(self, data):
        """ Export filtered observations in xls
        """
        now = datetime.now()
        filename = 'EMRT-observations-%s-%s.xls' % (
            self.context.getId(),
            now.strftime("%Y%M%d%H%m")
        )

        book = tablib.Databook((self.extract_data(data),))

        response = self.request.response
        response.setHeader("content-type", "application/vnc.ms-excel")
        response.setHeader("Content-disposition", "attachment;filename=" + filename)
        response.write(book.xls)
        return


def _item_user(fun, self, user, item):
    return (user.getId(), item.getId(), item.modified())


def decorate(item):
    """ prepare a plain object, so that we can cache it in a RAM cache """
    user = api.user.get_current()
    roles = api.user.get_roles(username=user.getId(), obj=item, inherit=False)
    new_item = {}
    new_item['absolute_url'] = item.absolute_url()
    new_item['observation_css_class'] = item.observation_css_class()
    new_item['getId'] = item.getId()
    new_item['Title'] = item.Title()
    new_item['observation_is_potential_significant_issue'] = item.observation_is_potential_significant_issue()
    new_item['observation_is_potential_technical_correction'] = item.observation_is_potential_technical_correction()
    new_item['observation_is_technical_correction'] = item.observation_is_technical_correction()
    new_item['text'] = item.text
    new_item['nfr_code_value'] = item.nfr_code_value()
    new_item['modified'] = item.modified()
    new_item['observation_phase'] = item.observation_phase()
    new_item['observation_question_status'] = item.observation_question_status()
    new_item['last_answer_reply_number'] = item.last_answer_reply_number()
    new_item['get_status'] = item.get_status()
    new_item['observation_already_replied'] = item.observation_already_replied()
    new_item['reply_comments_by_mse'] = item.reply_comments_by_mse()
    new_item['observation_finalisation_reason'] = item.observation_finalisation_reason()
    new_item['isCP'] = 'CounterPart' in roles
    new_item['isMSA'] = 'MSAuthority' in roles
    return new_item


def _catalog_change(fun, self, *args, **kwargs):
    counter = api.portal.get_tool('portal_catalog').getCounter()
    user = api.user.get_current().getId()
    path = '/'.join(self.context.getPhysicalPath())
    return (counter, user, path)


class Inbox2ReviewFolderView(grok.View):
    grok.context(IReviewFolder)
    grok.require('zope2.View')
    grok.name('inboxview2')

    def update(self):
        freeText = self.request.form.get('freeText', '')
        self.observations = self.get_all_observations(freeText)

    @cache(_catalog_change)
    @timeit
    def get_all_observations(self, freeText):
        catalog = api.portal.get_tool('portal_catalog')
        path = '/'.join(self.context.getPhysicalPath())
        query = {
            'path': path,
            'portal_type': 'Observation',
            'sort_on': 'modified',
            'sort_order': 'reverse',
        }
        if freeText != "":
            query['SearchableText'] = freeText
        import pdb; pdb.set_trace()
        return map(decorate, [b.getObject() for b in catalog.searchResults(query)])

    """
        Sector Expert
    """



    def get_draft_observations(self):
        """
         Role: Sector Expert
         without actions for LR, counterpart or MS
        """
        items = []
        for item in self.observations:
            if item.get('observation_question_status', '') in [
                    'observation-phase2-draft']:
                items.append(item)
        return items



    def get_draft_questions(self):
        """
         Role: Sector Expert
         with comments from counterpart or LR
        """
        items = []
        for item in self.observations:
            if item.get('observation_question_status', '') in [
                    'phase2-draft',
                    'phase2-counterpart-comments']:
                items.append(item)
        return items

    @ram.cache(_item_user)
    def get_roles_for_item(self, user, item):
        return api.user.get_roles(username=user.id, obj=item, inherit=False)



    def get_counterpart_questions_to_comment(self):
        """
         Role: Sector Expert
         needing comment from me
        """
        items = []
        for item in self.observations:
            # roles = self.get_roles_for_item(user, item)
            if item.get('observation_question_status', '') in [
                    'phase2-counterpart-comments'] and \
                    item.get('isCP', ''):
                items.append(item)
        return items


    def get_counterpart_conclusion_to_comment(self):
        """
         Role: Sector Expert
         needing comment from me
        """
        items = []
        for obj in self.observations:
            # roles = self.get_roles_for_item(user, obj)
            if obj.get('observation_question_status', '') in [
                    'phase2-conclusion-discussion'] and \
                    obj.get('isCP', ''):
                items.append(obj)
        return items


    def get_ms_answers_to_review(self):
        """
         Role: Sector Expert
         that need review
        """
        # user = api.user.get_current()
        # mtool = api.portal.get_tool('portal_membership')
        items = []
        for obj in self.observations:
            if obj.get('observation_question_status', '') in [
                    'phase2-answered',
                    ] or \
                    (obj.get('get_status') in [
                        'phase2-pending',
                        ] and \
                    obj.get('observation_question_status', '') in [
                        'phase2-closed',
                    ]):
                items.append(obj)
        return items



    def get_unanswered_questions(self):
        """
         Role: Sector Expert
         my questions sent to LR and MS and waiting for reply
        """
        items = []

        statuses = [
            'phase2-pending',
            'phase2-recalled-msa',
            'phase2-expert-comments',
            'phase2-pending-answer-drafting'
        ]

        # For a SE, those on LR pending to be sent to the MS
        # or recalled by him, are unanswered questions
        if self.is_sector_expert():
            statuses.extend([
                'phase2-drafted',
                'phase2-recalled-lr']
            )

        for obj in self.observations:
            if obj.get('observation_question_status', '') in statuses:
                items.append(obj)
        return items

    def get_waiting_for_comment_from_counterparts_for_question(self):
        """
         Role: Sector Expert
        """
        # user = api.user.get_current()
        # mtool = api.portal.get_tool('portal_membership')
        items = []
        for obj in self.observations:
            # roles = self.get_roles_for_item(user, obj)
            if obj.get('observation_question_status', '') in [
                    'phase2-counterpart-comments'] and \
                    obj.get('isCP', ''):
                items.append(obj)
        return items

    def get_waiting_for_comment_from_counterparts_for_conclusion(self):
        """
         Role: Sector Expert
        """
        # user = api.user.get_current()
        # mtool = api.portal.get_tool('portal_membership')
        items = []
        for obj in self.observations:
            # roles = self.get_roles_for_item(user, obj)
            if obj.get('observation_question_status', '') in [
                    'phase2-conclusion-discussion'] and \
                    obj.get('isCP', ''):
                items.append(obj)
        return items

    def get_observation_for_finalisation(self):
        """
         Role: Sector Expert
         waiting approval from LR
        """
        items = []
        for obj in self.observations:
            if obj.get('observation_question_status', '') in [
                    'phase2-conclusions',
                    'phase2-close-requested',]:
                items.append(obj)
        return items

    """
        Lead Reviewer
    """

    def get_questions_to_be_sent(self):
        """
         Role: Lead Reviewer
         Questions waiting for me to send to the MS
        """
        items = []
        for obj in self.observations:
            if obj.get('observation_question_status', '') in [
                    'phase2-drafted',
                    'phase2-recalled-lr']:
                items.append(obj)
        return items

    def get_observations_to_finalise(self):
        """
         Role: Lead Reviewer
         Observations waiting for me to confirm finalisation
        """
        items = []
        for obj in self.observations:
            if obj.get('observation_question_status', '') in [
                    'phase2-close-requested']:
                items.append(obj)
        return items

    def get_questions_to_comment(self):
        """
         Role: Lead Reviewer
         Questions waiting for my comments
        """
        items = []
        for obj in self.observations:
            # roles = self.get_roles_for_item(user, obj)
            if obj.get('observation_question_status', '') in [
                    'phase2-counterpart-comments'] and \
                    obj.get('isCP', ''):
                items.append(obj)
        return items



    def get_conclusions_to_comment(self):
        """
         Role: Lead Reviewer
         Conclusions waiting for my comments
        """
        items = []
        for obj in self.observations:
            # roles = self.get_roles_for_item(user, obj)
            if obj.get('observation_question_status', '') in [
                    'phase2-conclusion-discussion'] and \
                    obj.get('isCP', ''):
                items.append(obj)
        return items



    def get_questions_with_comments_from_reviewers(self):
        """
         Role: Lead Reviewer
         Questions waiting for comments by counterpart
        """
        items = []
        for obj in self.observations:
            # roles = self.get_roles_for_item(user, obj)
            if obj.get('observation_question_status', '') in [
                    'phase2-counterpart-comments'] and \
                    obj.get('isCP', ''):
                items.append(obj)
        return items



    def get_answers_from_ms(self):
        """
         Role: Lead Reviewer
         that need review by Sector Expert
        """
        items = []
        for obj in self.observations:
            if obj.get('observation_question_status', '') in [
                    'phase2-answered']:
                items.append(obj)
        return items



    def get_unanswered_questions_lr(self):
        """
         Role: Lead Reviewer
         questions waiting for comments from MS
        """
        items = []
        for obj in self.observations:
            if obj.get('observation_question_status', '') in [
                    'phase2-pending',
                    'phase2-recalled-msa',
                    'phase2-expert-comments',
                    'phase2-pending-answer-drafting']:
                items.append(obj)
        return items

    """
        MS Coordinator
    """

    def get_questions_to_be_answered(self):
        """
         Role: MS Coordinator
         Questions from the SE to be answered
        """
        items = []
        for obj in self.observations:
            # roles = self.get_roles_for_item(user, obj)
            if obj.get('observation_question_status', '') in [
                    'phase2-pending',
                    'phase2-recalled-msa',
                    'phase2-pending-answer-drafting'] and obj.get('isMSA', ''):
                items.append(obj)
        return items

    def get_questions_with_comments_received_from_mse(self):
        """
         Role: MS Coordinator
         Comments received from MS Experts
        """
        items = []
        for obj in self.observations:
            if obj.get('observation_question_status', '') in [
                    'phase2-expert-comments'] and \
                    obj.get('last_answer_reply_number') > 0:
                items.append(obj)
        return items

    def get_answers_requiring_comments_from_mse(self):
        """
         Role: MS Coordinator
         Answers requiring comments/discussion from MS experts
        """
        items = []
        for obj in self.observations:
            if obj.get('observation_question_status', '') in [
                    'phase2-expert-comments']:
                items.append(obj)
        return items

    def get_answers_sent_to_se_re(self):
        """
         Role: MS Coordinator
         Answers sent to SE
        """
        items = []
        for obj in self.observations:
            if (obj.get('observation_question_status', '') in
                    ['phase2-answered'] or
                    obj.get('observation_already_replied')) and \
                    obj.get('get_status', '') not in [
                        'phase2-closed']:
                items.append(obj)
        return items
    """
        MS Expert
    """

    def get_questions_with_comments_for_answer_needed_by_msc(self):
        """
         Role: MS Expert
         Comments for answer needed by MS Coordinator
        """
        items = []
        for obj in self.observations:
            if obj.get('observation_question_status', '') in [
                    'phase2-expert-comments']:
                items.append(obj)
        return items

    def get_observations_with_my_comments(self):
        """
         Role: MS Expert
         Observation I have commented on
        """
        items = []
        for obj in self.observations:
            if obj.get('observation_question_status', '') in [
                    'phase2-expert-comments',
                    'phase2-pending-answer-drafting'] and \
                    obj.get('reply_comments_by_mse'):
                items.append(obj)
        return items

    def get_observations_with_my_comments_sent_to_se_re(self):
        """
         Role: MS Expert
         Answers that I commented on sent to Sector Expert
        """
        items = []
        for obj in self.observations:
            if obj.get('observation_question_status', '') in [
                    'phase2-answered',
                    'phase2-recalled-msa'] and \
                    obj.get('reply_comments_by_mse'):
                items.append(obj)
        return items

    """
        Finalised observations
    """

    def get_no_response_needed_observations(self):
        """
         Finalised with 'no response needed'
        """
        items = []
        for obj in self.observations:
            if obj.get('observation_question_status', '') in [
                    'phase2-closed'] and \
                    obj.get('observation_finalisation_reason', '') == 'no-response-needed':
                items.append(obj)
        return items

    def get_resolved_observations(self):
        """
         Finalised with 'resolved'
        """
        items = []
        for obj in self.observations:
            if obj.get('observation_question_status', '') in [
                    'phase2-closed'] and \
                    obj.get('observation_finalisation_reason', '') == 'resolved':
                items.append(obj)
        return items

    def get_unresolved_observations(self):
        """
         Finalised with 'unresolved'
        """
        items = []
        for obj in self.observations:
            if obj.get('observation_question_status', '') in [
                    'phase2-closed'] and \
                    obj.get('observation_finalisation_reason', '') == 'unresolved':
                items.append(obj)
        return items

    def get_partly_resolved_observations(self):
        """
         Finalised with 'partly resolved'
        """
        items = []
        for obj in self.observations:
            if obj.get('observation_question_status', '') in [
                    'phase2-closed'] and \
                    obj.get('observation_finalisation_reason', '') == 'partly-resolved':
                items.append(obj)
        return items

    def get_technical_correction_observations(self):
        """
         Finalised with 'technical correction'
        """
        items = []
        for obj in self.observations:
            if obj.get('observation_question_status', '') in [
                    'phase2-closed'] and \
                    obj.get('observation_finalisation_reason', '') == 'technical-correction':
                items.append(obj)
        return items

    def get_revised_estimate_observations(self):
        """
         Finalised with 'partly resolved'
        """
        items = []
        for obj in self.observations:
            if obj.get('observation_question_status', '') in [
                    'phase2-closed'] and \
                    obj.get('observation_finalisation_reason', '') == 'revised-estimate':
                items.append(obj)
        return items

    def can_add_observation(self):
        sm = getSecurityManager()
        return sm.checkPermission('emrt.necd.content: Add Observation', self)

    def is_secretariat(self):
        user = api.user.get_current()
        return 'Manager' in user.getRoles()

    @cache(_user_name)
    def get_author_name(self, userid):
        user = api.user.get(userid)
        return user.getProperty('fullname', userid)

    def get_countries(self):
        vtool = getToolByName(self, 'portal_vocabularies')
        voc = vtool.getVocabularyByName('eea_member_states')
        countries = []
        voc_terms = voc.getDisplayList(self).items()
        for term in voc_terms:
            countries.append((term[0], term[1]))

        return countries

    def get_sectors(self):
        vtool = getToolByName(self, 'portal_vocabularies')
        voc = vtool.getVocabularyByName('ghg_source_sectors')
        sectors = []
        voc_terms = voc.getDisplayList(self).items()
        for term in voc_terms:
            sectors.append((term[0], term[1]))

        return sectors

    def is_sector_expert(self):
        user = api.user.get_current()
        user_groups = user.getGroups()
        return LDAP_SECTOREXP in user_groups

    def is_lead_reviewer(self):
        user = api.user.get_current()
        user_groups = user.getGroups()
        return LDAP_LEADREVIEW in user_groups

    def is_member_state_coordinator(self):
        user = api.user.get_current()
        return LDAP_MSA in user.getGroups()

    def is_member_state_expert(self):
        user = api.user.get_current()
        return LDAP_MSEXPERT in user.getGroups()


class InboxReviewFolderView(grok.View):
    grok.context(IReviewFolder)
    grok.require('zope2.View')
    grok.name('inboxview4')

    def can_add_observation(self):
        sm = getSecurityManager()
        return sm.checkPermission('emrt.necd.content: Add Observation', self)


class RoleMapItem(object):

    def __init__(self, roles):
        self.isCP = 'CounterPart' in roles
        self.isMSA = 'MSAuthority' in roles
        self.isRE = 'SectorExpert' in roles
        self.isLR = 'LeadReviewer' in roles

    def check_roles(self, rolename):
        if rolename == 'CounterPart':
            return self.isCP
        elif rolename == 'MSAuthority':
            return self.isMSA
        elif rolename == 'SectorExpert':
            return self.isRE
        elif rolename == 'NotCounterPartPhase2':
            return not self.isCP and self.isRE
        elif rolename == 'LeadReviewer':
            return self.isLR
        return False


class Inbox3ReviewFolderView(grok.View):
    grok.context(IReviewFolder)
    grok.require('zope2.View')
    grok.name('inboxview')

    @memoize
    def get_current_user(self):
        return api.user.get_current()


    def rolemap(self, observation):
        """ prepare a plain object, so that we can cache it in a RAM cache """
        user = self.get_current_user()
        roles = user.getRolesInContext(observation)
        return RoleMapItem(roles)

    def update(self):
        self.rolemap_observations = {}

    def batch(self, observations, b_size, b_start, orphan, b_start_str):
        observationsBatch = Batch(observations, int(b_size), int(b_start), orphan=1)
        observationsBatch.batchformkeys = []
        observationsBatch.b_start_str = b_start_str
        return observationsBatch

    def get_observations(self, rolecheck=None, **kw):
        freeText = self.request.form.get('freeText', '')
        catalog = api.portal.get_tool('portal_catalog')
        path = '/'.join(self.context.getPhysicalPath())
        query = {
            'path': path,
            'portal_type': 'Observation',
            'sort_on': 'modified',
            'sort_order': 'reverse',
        }
        if freeText:
            query['SearchableText'] = freeText

        query.update(kw)
        #from logging import getLogger
        #log = getLogger(__name__)

        observations = [b.getObject() for b in catalog.searchResults(query)]
        if rolecheck is None:
            #log.info('Querying Catalog: %s' % query)
            return observations

        for obs in observations:
            if obs.getId() not in self.rolemap_observations:
                self.rolemap_observations[obs.getId()] = self.rolemap(obs)

        #log.info('Querying Catalog with Rolecheck %s: %s ' % (rolecheck, query))

        def makefilter(rolename):
            """
            https://stackoverflow.com/questions/7045754/python-list-filtering-with-arguments
            """
            def myfilter(x):
                rolemap = self.rolemap_observations[x.getId()]
                return rolemap.check_roles(rolename)
            return myfilter

        filterfunc = makefilter(rolecheck)

        return filter(
            filterfunc,
            observations
        )

    @timeit
    def get_draft_observations(self):
        """
         Role: Sector Expert
         without actions for LR, counterpart or MS
        """
        phase2 = self.get_observations(
            rolecheck='SectorExpert',
            observation_question_status=[
                'observation-phase2-draft'])

        return phase2

    @timeit
    def get_draft_questions(self):
        """
         Role: Sector Expert
         with comments from counterpart or LR
        """
        phase2 = self.get_observations(
            rolecheck='SectorExpert',
            observation_question_status=[
                'phase2-draft',
                'phase2-drafted'])

        """
         Add also finalised observations with "no conclusion yet"
         https://taskman.eionet.europa.eu/issues/28813#note-5
        """
        no_conclusion_yet = self.get_observations(
            observation_question_status=['phase2-closed'],
            observation_finalisation_reason='no-conclusion-yet',
        )

        return phase2 + no_conclusion_yet

    @timeit
    def get_counterpart_questions_to_comment(self):
        """
         Role: Sector Expert
         needing comment from me
        """
        return self.get_observations(
            rolecheck='CounterPart',
            observation_question_status=[
                'phase2-counterpart-comments'])

    @timeit
    def get_counterpart_conclusion_to_comment(self):
        """
         Role: Sector Expert
         needing comment from me
        """
        return self.get_observations(
            rolecheck='CounterPart',
            observation_question_status=['phase2-conclusion-discussion'])

    @timeit
    def get_ms_answers_to_review(self):
        """
         Role: Sector Expert
         that need review
        """
        # user = api.user.get_current()
        # mtool = api.portal.get_tool('portal_membership')

        answered_phase2 = self.get_observations(
            rolecheck='SectorExpert',
            observation_question_status=[
                'phase2-answered'])

        pending_phase2 = self.get_observations(
            rolecheck='SectorExpert',
            observation_question_status=['phase2-closed'],
            review_state=['phase2-pending'])

        return answered_phase2 + pending_phase2

    @timeit
    def get_approval_questions(self):
        """
         Role: Sector Expert
         my questions sent to LR and MS and waiting for reply
        """
        # For a SE, those on LR pending to be sent to the MS
        # or recalled by him, are unanswered questions

        if not self.is_sector_expert():
            return []

        statuses_phase2 = [
            'phase2-drafted',
            'phase2-recalled-lr'
        ]

        phase2 = self.get_observations(
            rolecheck="SectorExpert",
            observation_question_status=statuses_phase2)

        return phase2

    @timeit
    def get_unanswered_questions(self):
        """
         Role: Sector Expert
         my questions sent to LR and MS and waiting for reply
        """

        statuses_phase2 = [
            'phase2-pending',
            'phase2-recalled-msa',
            'phase2-expert-comments',
            'phase2-pending-answer-drafting'
        ]

        phase2 = self.get_observations(
            rolecheck="SectorExpert",
            observation_question_status=statuses_phase2)

        return phase2

    @timeit
    def get_waiting_for_comment_from_counterparts_for_question(self):
        """
         Role: Sector Expert
        """
        phase2 =  self.get_observations(
            rolecheck='NotCounterPartPhase2',
            observation_question_status=[
                'phase2-counterpart-comments'])

        return phase2

    @timeit
    def get_waiting_for_comment_from_counterparts_for_conclusion(self):
        """
         Role: Sector Expert
        """
        phase2 =  self.get_observations(
            rolecheck='NotCounterPartPhase2',
            observation_question_status=[
                'phase2-conclusion-discussion'])
        return phase2

    @timeit
    def get_observation_for_finalisation(self):
        """
         Role: Sector Expert
         waiting approval from LR
        """

        phase2 =  self.get_observations(
            rolecheck='SectorExpert',
            observation_question_status=[
                'phase2-close-requested'])

        return phase2

    """
        Lead Reviewer
    """
    @timeit
    def get_questions_to_be_sent(self):
        """
         Role: Lead Reviewer
         Questions waiting for me to send to the MS
        """
        phase2 = self.get_observations(
            rolecheck='LeadReviewer',
            observation_question_status=[
                'phase2-drafted',
                'phase2-recalled-lr'])

        return phase2

    @timeit
    def get_observations_to_finalise(self):
        """
         Role: Lead Reviewer
         Observations waiting for me to confirm finalisation
        """

        phase2 = self.get_observations(
            rolecheck='LeadReviewer',
            observation_question_status=[
                'phase2-close-requested'])

        return phase2

    @timeit
    def get_questions_to_comment(self):
        """
         Role: Lead Reviewer
         Questions waiting for my comments
        """
        return self.get_observations(
            rolecheck='CounterPart',
            observation_question_status=[
                'phase2-counterpart-comments'])

    @timeit
    def get_conclusions_to_comment(self):
        """
         Role: Lead Reviewer
         Conclusions waiting for my comments
        """
        return self.get_observations(
            rolecheck='CounterPart',
            observation_question_status=['phase2-conclusion-discussion'])

    @timeit
    def get_questions_with_comments_from_reviewers(self):
        """
         Role: Lead Reviewer
         Questions waiting for comments by counterpart
        """
        return self.get_observations(
            rolecheck='CounterPart',
            observation_question_status=['phase2-counterpart-comments'])

    @timeit
    def get_answers_from_ms(self):
        """
         Role: Lead Reviewer
         that need review by Sector Expert
        """
        phase2 = self.get_observations(
            rolecheck='LeadReviewer',
            observation_question_status=[
                'phase2-answered'])
        return phase2

    @timeit
    def get_unanswered_questions_lr(self):
        """
         Role: Lead Reviewer
         questions waiting for comments from MS
        """

        phase2 = self.get_observations(
            rolecheck='LeadReviewer',
            observation_question_status=[
                'phase2-pending',
                'phase2-recalled-msa',
                'phase2-expert-comments',
                'phase2-pending-answer-drafting'])

        return phase2

    """
        MS Coordinator
    """
    @timeit
    def get_questions_to_be_answered(self):
        """
         Role: MS Coordinator
         Questions from the SE to be answered
        """
        return self.get_observations(
            rolecheck='MSAuthority',
            observation_question_status=[
                'phase2-pending',
                'phase2-recalled-msa',
                'phase2-pending-answer-drafting'])

    @timeit
    def get_questions_with_comments_received_from_mse(self):
        """
         Role: MS Coordinator
         Comments received from MS Experts
        """
        return self.get_observations(
            rolecheck='MSAuthority',
            observation_question_status=['phase2-expert-comments'],
            last_answer_has_replies=True,
            # last_answer_reply_number > 0
        )

    @timeit
    def get_answers_requiring_comments_from_mse(self):
        """
         Role: MS Coordinator
         Answers requiring comments/discussion from MS experts
        """
        return self.get_observations(
            observation_question_status=['phase2-expert-comments'],
        )

    @timeit
    def get_answers_sent_to_se_re(self):
        """
         Role: MS Coordinator
         Answers sent to SE
        """
        answered = self.get_observations(
            observation_question_status=['phase2-answered'])
        cat = api.portal.get_tool('portal_catalog')
        statuses = list(cat.uniqueValuesFor('review_state'))
        try:
            statuses.remove('phase2-closed')
        except ValueError:
            pass
        not_closed = self.get_observations(
            review_state=statuses,
            observation_already_replied=True)

        return list(set(answered + not_closed))

    """
        MS Expert
    """
    @timeit
    def get_questions_with_comments_for_answer_needed_by_msc(self):
        """
         Role: MS Expert
         Comments for answer needed by MS Coordinator
        """
        return self.get_observations(
            observation_question_status=['phase2-expert-comments'])

    @timeit
    def get_observations_with_my_comments(self):
        """
         Role: MS Expert
         Observation I have commented on
        """
        return self.get_observations(
            observation_question_status=[
                'phase2-expert-comments',
                'phase2-pending-answer-drafting'],
            reply_comments_by_mse=True,
        )

    @timeit
    def get_observations_with_my_comments_sent_to_se_re(self):
        """
         Role: MS Expert
         Answers that I commented on sent to Sector Expert
        """
        return self.get_observations(
            observation_question_status=[
                'phase2-answered',
                'phase2-recalled-msa'],
            reply_comments_by_mse=True,
        )

    def can_add_observation(self):
        sm = getSecurityManager()
        return sm.checkPermission('emrt.necd.content: Add Observation', self)

    def is_secretariat(self):
        user = api.user.get_current()
        return 'Manager' in user.getRoles()

    @cache(_user_name)
    def get_author_name(self, userid):
        user = api.user.get(userid)
        return user.getProperty('fullname', userid)

    def get_countries(self):
        vtool = getToolByName(self, 'portal_vocabularies')
        voc = vtool.getVocabularyByName('eea_member_states')
        countries = []
        voc_terms = voc.getDisplayList(self).items()
        for term in voc_terms:
            countries.append((term[0], term[1]))

        return countries

    def get_sectors(self):
        vtool = getToolByName(self, 'portal_vocabularies')
        voc = vtool.getVocabularyByName('ghg_source_sectors')
        sectors = []
        voc_terms = voc.getDisplayList(self).items()
        for term in voc_terms:
            sectors.append((term[0], term[1]))

        return sectors

    def is_sector_expert(self):
        user = api.user.get_current()
        user_groups = user.getGroups()
        return LDAP_SECTOREXP in user_groups

    def is_lead_reviewer(self):
        user = api.user.get_current()
        user_groups = user.getGroups()
        return LDAP_LEADREVIEW in user_groups

    def is_member_state_coordinator(self):
        user = api.user.get_current()
        return LDAP_MSA in user.getGroups()

    def is_member_state_expert(self):
        user = api.user.get_current()
        return LDAP_MSEXPERT in user.getGroups()


class FirstObservation(Inbox3ReviewFolderView):
    grok.context(IReviewFolder)
    grok.name('get-first-reviewable-observation')
    grok.require('zope2.View')

    def update(self):
        super(FirstObservation, self).update()
        url = ''
        obs = self.get_draft_observations()
        if obs:
            url = obs[0].absolute_url()

        return self.request.response.redirect(url)

    def render(self):
        return ''

class FinalisedFolderView(grok.View):
    grok.context(IReviewFolder)
    grok.require('zope2.View')
    grok.name('finalisedfolderview')

    def batch(self, observations, b_size, b_start, orphan, b_start_str):
        observationsBatch = Batch(observations, int(b_size), int(b_start), orphan=1)
        observationsBatch.batchformkeys = []
        observationsBatch.b_start_str = b_start_str
        return observationsBatch

    @cache(_catalog_change)
    @timeit
    def get_all_observations(self, freeText):
        catalog = api.portal.get_tool('portal_catalog')
        path = '/'.join(self.context.getPhysicalPath())
        query = {
            'path': path,
            'portal_type': 'Observation',
            'sort_on': 'modified',
            'sort_order': 'reverse',
        }
        if freeText != "":
            query['SearchableText'] = freeText

        return map(decorate, [b.getObject() for b in catalog.searchResults(query)])

    def get_observations(self, rolecheck=None, **kw):
        freeText = self.request.form.get('freeText', '')
        catalog = api.portal.get_tool('portal_catalog')
        path = '/'.join(self.context.getPhysicalPath())
        query = {
            'path': path,
            'portal_type': 'Observation',
            'sort_on': 'modified',
            'sort_order': 'reverse',
        }
        if freeText:
            query['SearchableText'] = freeText

        query.update(kw)
        #from logging import getLogger
        #log = getLogger(__name__)
        if rolecheck is None:
            #log.info('Querying Catalog: %s' % query)
            return [b.getObject() for b in catalog.searchResults(query)]
        else:
            #log.info('Querying Catalog with Rolecheck %s: %s ' % (rolecheck, query))

            def makefilter(rolename):
                """
                https://stackoverflow.com/questions/7045754/python-list-filtering-with-arguments
                """
                def myfilter(x):
                    if rolename == 'CounterPart':
                        return x.isCP
                    elif rolename == 'MSAuthority':
                        return x.isMSA
                    elif rolename == 'SectorExpert':
                        return x.isRE
                    elif rolename == 'NotCounterPartPhase2':
                        return not x.isCP and x.isRE
                    elif rolename == 'LeadReviewer':
                        return x.isLR
                    return False
                return myfilter

            filterfunc = makefilter(rolecheck)

            return filter(
                filterfunc,
                map(decorate2,
                    [b.getObject() for b in catalog.searchResults(query)])
            )

    """
        Finalised observations
    """
    @timeit
    def get_no_response_needed_observations(self):
        """
         Finalised with 'no response needed'
        """
        return self.get_observations(
            observation_question_status=['phase2-closed'],
            observation_finalisation_reason='no-response-needed',
        )

    @timeit
    def get_resolved_observations(self):
        """
         Finalised with 'resolved'
        """
        return self.get_observations(
            observation_question_status=['phase2-closed'],
            observation_finalisation_reason='resolved',
        )

    @timeit
    def get_unresolved_observations(self):
        """
         Finalised with 'unresolved'
        """
        return self.get_observations(
            observation_question_status=['phase2-closed'],
            observation_finalisation_reason='unresolved',
        )

    @timeit
    def get_partly_resolved_observations(self):
        """
         Finalised with 'partly resolved'
        """
        return self.get_observations(
            observation_question_status=['phase2-closed'],
            observation_finalisation_reason='partly-resolved',
        )

    @timeit
    def get_technical_correction_observations(self):
        """
         Finalised with 'technical correction'
        """
        return self.get_observations(
            observation_question_status=['phase2-closed'],
            observation_finalisation_reason='technical-correction',
        )

    @timeit
    def get_revised_estimate_observations(self):
        """
         Finalised with 'partly resolved'
        """
        return self.get_observations(
            observation_question_status=['phase2-closed'],
            observation_finalisation_reason='revised-estimate',
        )

    def can_add_observation(self):
        sm = getSecurityManager()
        return sm.checkPermission('emrt.necd.content: Add Observation', self)

    def is_secretariat(self):
        user = api.user.get_current()
        return 'Manager' in user.getRoles()

    @cache(_user_name)
    def get_author_name(self, userid):
        user = api.user.get(userid)
        return user.getProperty('fullname', userid)

    def get_countries(self):
        vtool = getToolByName(self, 'portal_vocabularies')
        voc = vtool.getVocabularyByName('eea_member_states')
        countries = []
        voc_terms = voc.getDisplayList(self).items()
        for term in voc_terms:
            countries.append((term[0], term[1]))

        return countries

    def get_sectors(self):
        vtool = getToolByName(self, 'portal_vocabularies')
        voc = vtool.getVocabularyByName('ghg_source_sectors')
        sectors = []
        voc_terms = voc.getDisplayList(self).items()
        for term in voc_terms:
            sectors.append((term[0], term[1]))

        return sectors

    def is_sector_expert(self):
        user = api.user.get_current()
        user_groups = user.getGroups()
        return LDAP_SECTOREXP in user_groups

    def is_lead_reviewer(self):
        user = api.user.get_current()
        user_groups = user.getGroups()
        return LDAP_LEADREVIEW in user_groups

    def is_member_state_coordinator(self):
        user = api.user.get_current()
        return LDAP_MSA in user.getGroups()

    def is_member_state_expert(self):
        user = api.user.get_current()
        return LDAP_MSEXPERT in user.getGroups()
