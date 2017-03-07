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
from emrt.necd.content.constants import ROLE_MSA
from emrt.necd.content.constants import ROLE_MSE
from emrt.necd.content.constants import ROLE_SE
from emrt.necd.content.constants import ROLE_LR
from emrt.necd.content.constants import ROLE_CP

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

        if country != "":
            query['Country'] = country
        if status != "":
            if status != "open":
                query['observation_finalisation_reason'] = status
            else:
                query['review_state'] = [
                    'pending',
                    'close-requested',
                    'draft',
                    'conclusions',
                    'conclusion-discussion',
                ]

        if reviewYear != "":
            query['review_year'] = reviewYear
        if inventoryYear != "":
            query['year'] = inventoryYear
        if highlights != "":
            query['highlight'] = highlights.split(",")
        if freeText != "":
            query['SearchableText'] = freeText
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
        review_years = [
            c for c in catalog.uniqueValuesFor('review_year') if
            isinstance(c, basestring)
        ]
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
        """ Vocabularies are used to fetch available reasons.
            This used to have hardcoded values for 2015 and 2016.
            Currently it works like this:
                - try to get vocabulary values that end
                  in the current folder title (e.g. "resolved2016")
                - if no values match, get the values which don't
                  end in an year (e.g. "resolved")
            This covers the previous functionality while also supporting
            any number of upcoming years, as well as "Test"-type
            review folders.
        """
        vtool = getToolByName(self, 'portal_vocabularies')
        reasons = [('open', 'open')]

        context_title = self.context.Title().strip()

        vocab_ids = ('conclusion_reasons', )

        to_add = []
        all_terms = []

        for vocab_id in vocab_ids:
            voc = vtool.getVocabularyByName(vocab_id)
            voc_terms = voc.getDisplayList(self).items()
            all_terms.extend(voc_terms)

        # if term ends in the review folder title (e.g. 2016)
        for term_key, term_title in all_terms:
            if term_key.endswith(context_title):
                to_add.append((term_key, term_title))

        # if no matching term keys were found,
        # use those that don't end in a year
        if not to_add:
            for term_key, term_title in all_terms:
                if not term_key[-4:].isdigit():
                    to_add.append((term_key, term_title))

        reasons.extend(to_add)
        return reasons

    def is_member_state_coordinator(self):
        if api.user.is_anonymous():
            raise Unauthorized
        user = api.user.get_current()
        roles = api.user.get_roles(
            user=user,
            obj=self.context
        )
        return ROLE_MSA in roles

    def is_member_state_expert(self):
        user = api.user.get_current()
        roles = api.user.get_roles(
            user=user,
            obj=self.context
        )
        return ROLE_MSE in roles


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
    ('observation_finalisation_reason', 'Conclusion'),
    ('observation_finalisation_text', 'Conclusion note'),
    ('observation_status', 'Workflow'),
    ('get_author_name', 'Author')
])

# Don't show conclusion notes to MS users.
EXCLUDE_FIELDS_FOR_MS = (
    'observation_finalisation_text',
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
    new_item['observation_question_status'] = item.observation_question_status()
    new_item['last_answer_reply_number'] = item.last_answer_reply_number()
    new_item['get_status'] = item.get_status()
    new_item['observation_already_replied'] = item.observation_already_replied()
    new_item['reply_comments_by_mse'] = item.reply_comments_by_mse()
    new_item['observation_finalisation_reason'] = item.observation_finalisation_reason()
    new_item['isCP'] = ROLE_CP in roles
    new_item['isMSA'] = ROLE_MSA in roles
    return new_item


def _catalog_change(fun, self, *args, **kwargs):
    counter = api.portal.get_tool('portal_catalog').getCounter()
    user = api.user.get_current().getId()
    path = '/'.join(self.context.getPhysicalPath())
    return (counter, user, path)


class RoleMapItem(object):

    def __init__(self, roles):
        self.isCP = ROLE_CP in roles
        self.isMSA = ROLE_MSA in roles
        self.isSE = ROLE_SE in roles
        self.isLR = ROLE_LR in roles

    def check_roles(self, rolename):
        if rolename == ROLE_CP:
            return self.isCP
        elif rolename == ROLE_MSA:
            return self.isMSA
        elif rolename == ROLE_SE:
            return self.isSE
        elif rolename == 'NotCounterPart':
            return not self.isCP and self.isSE
        elif rolename == ROLE_LR:
            return self.isLR
        return False


class InboxReviewFolderView(grok.View):
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
        observationsBatch = Batch(
            observations, int(b_size), int(b_start), orphan=1)
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

        observations = [b.getObject() for b in catalog.searchResults(query)]
        if rolecheck is None:
            return observations

        for obs in observations:
            if obs.getId() not in self.rolemap_observations:
                self.rolemap_observations[obs.getId()] = self.rolemap(obs)

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
        return self.get_observations(
            rolecheck=ROLE_SE,
            observation_question_status=[
                'observation-draft'])

    @timeit
    def get_draft_questions(self):
        """
         Role: Sector Expert
         with comments from counterpart or LR
        """
        conclusions = self.get_observations(
            rolecheck=ROLE_SE,
            observation_question_status=[
                'draft',
                'drafted'])

        """
         Add also finalised observations with "no conclusion yet"
         https://taskman.eionet.europa.eu/issues/28813#note-5
        """
        no_conclusion_yet = self.get_observations(
            observation_question_status=['closed'],
            observation_finalisation_reason='no-conclusion-yet',
        )

        return conclusions + no_conclusion_yet

    @timeit
    def get_counterpart_questions_to_comment(self):
        """
         Role: Sector Expert
         needing comment from me
        """
        return self.get_observations(
            rolecheck=ROLE_CP,
            observation_question_status=[
                'counterpart-comments'])

    @timeit
    def get_counterpart_conclusion_to_comment(self):
        """
         Role: Sector Expert
         needing comment from me
        """
        return self.get_observations(
            rolecheck=ROLE_CP,
            observation_question_status=['conclusion-discussion'])

    @timeit
    def get_ms_answers_to_review(self):
        """
         Role: Sector Expert
         that need review
        """
        # user = api.user.get_current()
        # mtool = api.portal.get_tool('portal_membership')

        answered = self.get_observations(
            rolecheck=ROLE_SE,
            observation_question_status=[
                'answered'])

        pending = self.get_observations(
            rolecheck=ROLE_SE,
            observation_question_status=['closed'],
            review_state=['pending'])

        return answered + pending

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

        statuses = [
            'drafted',
            'recalled-lr'
        ]

        return self.get_observations(
            rolecheck=ROLE_SE,
            observation_question_status=statuses)


    @timeit
    def get_unanswered_questions(self):
        """
         Role: Sector Expert
         my questions sent to LR and MS and waiting for reply
        """

        statuses = [
            'pending',
            'recalled-msa',
            'expert-comments',
            'pending-answer-drafting'
        ]

        return self.get_observations(
            rolecheck=ROLE_SE,
            observation_question_status=statuses)


    @timeit
    def get_waiting_for_comment_from_counterparts_for_question(self):
        """
         Role: Sector Expert
        """
        return self.get_observations(
            rolecheck='NotCounterPart',
            observation_question_status=[
                'counterpart-comments'])

    @timeit
    def get_waiting_for_comment_from_counterparts_for_conclusion(self):
        """
         Role: Sector Expert
        """
        return  self.get_observations(
            rolecheck='NotCounterPart',
            observation_question_status=[
                'conclusion-discussion'])

    @timeit
    def get_observation_for_finalisation(self):
        """
         Role: Sector Expert
         waiting approval from LR
        """

        return  self.get_observations(
            rolecheck=ROLE_SE,
            observation_question_status=[
                'close-requested'])



    """
        Lead Reviewer
    """
    @timeit
    def get_questions_to_be_sent(self):
        """
         Role: Lead Reviewer
         Questions waiting for me to send to the MS
        """
        return self.get_observations(
            rolecheck=ROLE_LR,
            observation_question_status=[
                'drafted',
                'recalled-lr'])



    @timeit
    def get_observations_to_finalise(self):
        """
         Role: Lead Reviewer
         Observations waiting for me to confirm finalisation
        """

        return self.get_observations(
            rolecheck=ROLE_LR,
            observation_question_status=[
                'close-requested'])



    @timeit
    def get_questions_to_comment(self):
        """
         Role: Lead Reviewer
         Questions waiting for my comments
        """
        return self.get_observations(
            rolecheck=ROLE_CP,
            observation_question_status=[
                'counterpart-comments'])

    @timeit
    def get_conclusions_to_comment(self):
        """
         Role: Lead Reviewer
         Conclusions waiting for my comments
        """
        return self.get_observations(
            rolecheck=ROLE_CP,
            observation_question_status=['conclusion-discussion'])

    @timeit
    def get_questions_with_comments_from_reviewers(self):
        """
         Role: Lead Reviewer
         Questions waiting for comments by counterpart
        """
        return self.get_observations(
            rolecheck=ROLE_CP,
            observation_question_status=['counterpart-comments'])

    @timeit
    def get_answers_from_ms(self):
        """
         Role: Lead Reviewer
         that need review by Sector Expert
        """
        return self.get_observations(
            rolecheck=ROLE_LR,
            observation_question_status=[
                'answered'])


    @timeit
    def get_unanswered_questions_lr(self):
        """
         Role: Lead Reviewer
         questions waiting for comments from MS
        """

        return self.get_observations(
            rolecheck=ROLE_LR,
            observation_question_status=[
                'pending',
                'recalled-msa',
                'expert-comments',
                'pending-answer-drafting'])



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
            rolecheck=ROLE_MSA,
            observation_question_status=[
                'pending',
                'recalled-msa',
                'pending-answer-drafting'])

    @timeit
    def get_questions_with_comments_received_from_mse(self):
        """
         Role: MS Coordinator
         Comments received from MS Experts
        """
        return self.get_observations(
            rolecheck=ROLE_MSA,
            observation_question_status=['expert-comments'],
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
            observation_question_status=['expert-comments'],
        )

    @timeit
    def get_answers_sent_to_se_re(self):
        """
         Role: MS Coordinator
         Answers sent to SE
        """
        answered = self.get_observations(
            observation_question_status=['answered'])
        cat = api.portal.get_tool('portal_catalog')
        statuses = list(cat.uniqueValuesFor('review_state'))
        try:
            statuses.remove('closed')
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
            observation_question_status=['expert-comments'])

    @timeit
    def get_observations_with_my_comments(self):
        """
         Role: MS Expert
         Observation I have commented on
        """
        return self.get_observations(
            observation_question_status=[
                'expert-comments',
                'pending-answer-drafting'],
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
                'answered',
                'recalled-msa'],
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
        roles = api.user.get_roles(
            user=user,
            obj=self.context
        )
        return ROLE_SE in roles

    def is_lead_reviewer(self):
        user = api.user.get_current()
        roles = api.user.get_roles(
            user=user,
            obj=self.context
        )
        return ROLE_LR in roles

    def is_member_state_coordinator(self):
        user = api.user.get_current()
        roles = api.user.get_roles(
            user=user,
            obj=self.context
        )
        return ROLE_MSA in roles

    def is_member_state_expert(self):
        user = api.user.get_current()
        roles = api.user.get_roles(
            user=user,
            obj=self.context
        )
        return ROLE_MSE in roles


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
                    if rolename == ROLE_CP:
                        return x.isCP
                    elif rolename == ROLE_MSA:
                        return x.isMSA
                    elif rolename == ROLE_SE:
                        return x.isSE
                    elif rolename == 'NotCounterPart':
                        return not x.isCP and x.isSE
                    elif rolename == ROLE_LR:
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
            observation_question_status=['closed'],
            observation_finalisation_reason='no-response-needed',
        )

    @timeit
    def get_resolved_observations(self):
        """
         Finalised with 'resolved'
        """
        return self.get_observations(
            observation_question_status=['closed'],
            observation_finalisation_reason='resolved',
        )

    @timeit
    def get_unresolved_observations(self):
        """
         Finalised with 'unresolved'
        """
        return self.get_observations(
            observation_question_status=['closed'],
            observation_finalisation_reason='unresolved',
        )

    @timeit
    def get_partly_resolved_observations(self):
        """
         Finalised with 'partly resolved'
        """
        return self.get_observations(
            observation_question_status=['closed'],
            observation_finalisation_reason='partly-resolved',
        )

    @timeit
    def get_technical_correction_observations(self):
        """
         Finalised with 'technical correction'
        """
        return self.get_observations(
            observation_question_status=['closed'],
            observation_finalisation_reason='technical-correction',
        )

    @timeit
    def get_revised_estimate_observations(self):
        """
         Finalised with 'partly resolved'
        """
        return self.get_observations(
            observation_question_status=['closed'],
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
        roles = api.user.get_roles(
            user=user,
            obj=self.context
        )
        return ROLE_SE in roles

    def is_lead_reviewer(self):
        user = api.user.get_current()
        roles = api.user.get_roles(
            user=user,
            obj=self.context
        )
        return ROLE_LR in roles

    def is_member_state_coordinator(self):
        user = api.user.get_current()
        roles = api.user.get_roles(
            user=user,
            obj=self.context
        )
        return ROLE_MSA in roles

    def is_member_state_expert(self):
        user = api.user.get_current()
        roles = api.user.get_roles(
            user=user,
            obj=self.context
        )
        return ROLE_MSE in roles
