import re
from functools import partial
from itertools import takewhile
from logging import getLogger

import openpyxl

from DateTime import DateTime
from zope.annotation.interfaces import IAnnotations
from zope.component import getUtility
from zope.component.hooks import getSite
from zope.interface import Invalid
from zope.schema.interfaces import IVocabularyFactory

from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage

from Products.CMFCore.utils import getToolByName

import plone.api as api
from plone.app.discussion.conversation import ANNOTATION_KEY

from emrt.necd.content.observation import _is_projection
from emrt.necd.content.observation import inventory_year
from emrt.necd.content.roles.localrolesubscriber import grant_local_roles

LOG = getLogger("emrt.necd.content.carryover")


R_OBS_ID = r"(\w+)-([\w\-\)\(\,\ ]+)-(\d+)-(\d+)"


class ReadId(object):
    def __init__(self, obs_id):
        self.match = re.match(R_OBS_ID, obs_id)
        self.result = self.match.groups()

        self.country_code = self.result[0]
        self.nfr_code = self.result[1]
        self.year = self.result[2]
        self.index = self.result[3]


def get_vocabulary_values(context, name):
    try:
        factory = getUtility(IVocabularyFactory, name)
        vocabulary = factory(context)
        return sorted([k for k, v in vocabulary.by_token.items()])
    except:
        return []


def read_int(value):
    result = 0
    if value:
        try:
            result = int(value)
        except (ValueError, TypeError):
            result = 0
    return result


def read_inventory_year(value):

    try:
        inventory_year(value)
        return value
    except Invalid:
        return 0
    except TypeError:
        return read_int(value)


def read_projection_year(value):
    value = str(value) if isinstance(value, (int, long)) else value
    years = read_list(value)
    proj_years = [u"2020", u"2025", u"2030", u"2040", u"2050"]
    is_correct = bool(set(years) & set(proj_years))
    if is_correct:
        return years
    return []


def read_list(value):
    result = []
    if value:
        splitted = re.split(r"[,\n]\s*", value)
        result = list(val.strip() for val in splitted)
    return result


def read_unicode(value):
    return value if value else u""


EXTRA_FIELDS = (
    ("text", read_unicode),
    ("review_year", read_int),
    ("year", read_inventory_year),
    ("nfr_code", read_unicode),
    ("pollutants", read_list),
)

EXTRA_FIELDS_PROJECTION = (
    ("text", read_unicode),
    ("review_year", read_int),
    ("year", read_projection_year),
    ("nfr_code", read_unicode),
    ("pollutants", read_list),
)


def _read_col(row, nr):
    val = row[nr].value
    return val.strip() if val and hasattr(val, "strip") else val


def _clear_local_roles(obj):
    obj.__ac_local_roles__ = None


def clear_and_grant_roles(obj):
    """Clear any local roles already granted and grant just those
    that make sense in the current review folder context.

    [refs #105604] This makes sure that users that were granted
    local roles on the old observation will not continue to
    have them (e.g. CounterPart).
    """
    _clear_local_roles(obj)
    grant_local_roles(obj)


def _copy_obj(target, ob, new_id=None):
    orig_ob = ob
    ob_id = new_id or orig_ob.getId()
    ob = ob._getCopy(target)
    ob._setId(ob_id)
    target._setObject(ob_id, ob)
    return target[ob_id]


def _copy_and_flag(context, obj, new_id=None):
    parse_id = ReadId(new_id or obj.getId())
    ob = _copy_obj(context, obj, new_id=new_id)
    ob.carryover_from = parse_id.year
    ob.review_year = int(parse_id.year)

    LOG.info(
        "Copied %s -> %s",
        obj.absolute_url(1),
        ob.absolute_url(1),
    )

    return ob


def _obj_from_url(context, site_url, url):
    traversable = str(url.split(site_url)[-1][1:])
    return context.unrestrictedTraverse(traversable)


def replace_conclusion_text(obj, text):
    conclusion = obj.get_conclusion()
    if text and conclusion:
        conclusion.text = text


def delete_conclusion_file(obj):
    conclusion = obj.get_conclusion()
    if conclusion:
        for ob in conclusion.values():
            if ob.portal_type == "NECDFile":
                conclusion.manage_delObjects([ob.getId()])


def clear_conclusion_discussion(obj):
    conclusion = obj.get_conclusion()
    if conclusion:
        annotations = IAnnotations(conclusion)
        if ANNOTATION_KEY in annotations:
            del annotations[ANNOTATION_KEY]


def clear_conclusion_closing_reason(obj):
    conclusion = obj.get_conclusion()
    if conclusion:
        conclusion.closing_reason = u""


def clear_conclusion_history(obj, wf_id):
    conclusion = obj.get_conclusion()
    if conclusion:
        cur_history = conclusion.workflow_history[wf_id]
        conclusion.workflow_history[wf_id] = (cur_history[0],)


def save_extra_fields(obj, extra_fields):
    for fname, fvalue in extra_fields.items():
        if fvalue:
            setattr(obj, fname, fvalue)


def prepend_qa(target, source):
    source_qa = source.get_question()
    target_qa = target.get_question()

    if source_qa and target_qa:
        for comment in source_qa.values():
            _copy_obj(target_qa, comment)

        ordering = target_qa.getOrdering()
        ordering.orderObjects(key="creation_date")

    elif source_qa and not target_qa:
        _copy_obj(target, source_qa)


def add_to_wh(wf, obj, action, state, actor):
    wh = obj.workflow_history
    wf_id = wf.getId()
    wh[wf_id] = wh[wf_id] + (
        {
            "comments": "Carryover force state",
            "actor": actor,
            "time": DateTime(),
            "action": action,
            "review_state": state,
        },
    )
    wf.updateRoleMappingsFor(obj)


def reopen_with_qa(wf, wf_q, wf_c, obj, actor):
    add_to_wh(wf, obj, "reopen-qa-chat", "pending", actor)
    question = obj.get_question()
    if question:
        add_to_wh(wf_q, question, "reopen", "draft", actor)

    conclusion = obj.get_conclusion()
    if conclusion:
        add_to_wh(wf_c, conclusion, "redraft", "draft", actor)


def read_extra_fields(row, row_nr, start_at, context):
    extra_fields = (
        EXTRA_FIELDS_PROJECTION
        if context.type == "projection"
        else EXTRA_FIELDS
    )
    result = dict()
    for idx, (fname, reader) in enumerate(extra_fields):
        col_idx = start_at + idx
        try:
            result[fname] = reader(_read_col(row, col_idx))
        except IndexError:
            msg = "Cannot read field {} on column {}, row {}.".format(
                fname, col_idx + 1, row_nr
            )
            request = api.env.getRequest()
            api.portal.show_message(msg, request=request, type="error")
            raise

    return result


def copy_direct(context, catalog, wf, wf_q, wf_c, obj_from_url, row, row_nr):
    source = _read_col(row, 0)
    conclusion_text = _read_col(row, 1)
    actor = _read_col(row, 2) or api.user.get_current().getId()
    extra_fields = read_extra_fields(row, row_nr, start_at=3, context=context)

    obj = obj_from_url(source)
    ob = _copy_and_flag(context, obj)

    replace_conclusion_text(ob, conclusion_text)
    clear_conclusion_discussion(ob)
    clear_conclusion_closing_reason(ob)
    clear_conclusion_history(ob, wf_c.getId())
    delete_conclusion_file(ob)
    save_extra_fields(ob, extra_fields)

    clear_and_grant_roles(ob)
    reopen_with_qa(wf, wf_q, wf_c, ob, actor)

    catalog.catalog_object(ob)


def copy_complex(context, catalog, wf, wf_q, wf_c, obj_from_url, row, row_nr):
    source = _read_col(row, 0)
    older_source = _read_col(row, 1)
    conclusion_text = _read_col(row, 2)
    actor = _read_col(row, 3)
    extra_fields = read_extra_fields(row, row_nr, start_at=4, context=context)

    obj = obj_from_url(source)
    older_obj = obj_from_url(older_source)

    ob = _copy_and_flag(context, obj, older_obj.getId())

    replace_conclusion_text(ob, conclusion_text)
    clear_conclusion_discussion(ob)
    clear_conclusion_closing_reason(ob)
    clear_conclusion_history(ob, wf_c.getId())
    delete_conclusion_file(ob)
    save_extra_fields(ob, extra_fields)

    prepend_qa(ob, older_obj)
    clear_and_grant_roles(ob)
    reopen_with_qa(wf, wf_q, wf_c, ob, actor)

    catalog.catalog_object(ob)


class CarryOverView(BrowserView):

    index = ViewPageTemplateFile("templates/carryover.pt")

    def __call__(self):
        values_for_pollutants = get_vocabulary_values(
            self.context, "emrt.necd.content.pollutants"
        )
        values_for_nfr_code = get_vocabulary_values(
            self.context, "emrt.necd.content.nfr_code"
        )
        return self.index(
            values_for_nfr_code=u", ".join(values_for_nfr_code),
            values_for_pollutants=u", ".join(values_for_pollutants),
            is_projection=self.context.type == "projection",
        )

    def start(self, action, xls):
        portal = getSite()
        wb = openpyxl.load_workbook(xls, read_only=True, data_only=True)
        sheet = wb.worksheets[0]

        sheet_rows = sheet.rows
        next(sheet_rows)  # skip first row (header)
        # extract rows with values
        valid_rows = tuple(
            takewhile(lambda row: any(c.value for c in row), sheet_rows)
        )

        context = self.context
        site_url = portal.absolute_url()
        obj_from_url = partial(_obj_from_url, context, site_url)
        catalog = getToolByName(portal, "portal_catalog")
        wft = getToolByName(portal, "portal_workflow")

        wf_obs = wft.getWorkflowById(wft.getChainFor("Observation")[0])
        wf_question = wft.getWorkflowById(wft.getChainFor("Question")[0])
        wf_conclusion = wft.getWorkflowById(wft.getChainFor("Conclusions")[0])

        actions = dict(direct=copy_direct, complex=copy_complex)
        copy_func = partial(
            actions[action],
            context,
            catalog,
            wf_obs,
            wf_question,
            wf_conclusion,
            obj_from_url,
        )

        for row_nr, row in enumerate(
            valid_rows, start=2
        ):  # start at 2 since we skip header
            copy_func(row, row_nr)

        if len(valid_rows) > 0:
            (
                IStatusMessage(self.request).add(
                    "Carryover successfull!", type="info"
                )
            )
        else:
            (
                IStatusMessage(self.request).add(
                    "No data provided!", type="warn"
                )
            )
        self.request.RESPONSE.redirect(context.absolute_url())
