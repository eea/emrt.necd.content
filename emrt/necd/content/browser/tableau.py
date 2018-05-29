import os
from datetime import datetime

from collections import defaultdict
from operator import itemgetter
from itertools import islice

from functools import partial
from functools import reduce

from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory

from Products.Five import BrowserView

from Products.CMFCore.utils import getToolByName

from openpyxl import load_workbook

from emrt.necd.content.utils import jsonify
from emrt.necd.content.reviewfolder import QUESTION_WORKFLOW_MAP


TOKEN = os.environ.get("TABLEAU_TOKEN")


SHEET_MS_ROLES = itemgetter(0)
SHEET_RS = itemgetter(1)

COL_MS__ROLES_MS = itemgetter(0)
COL_LR__ROLES_MS = itemgetter(1)
COL_SE__ROLES_MS = itemgetter(2)

COL_SE__RS = itemgetter(0)
COL_CAT__RS = itemgetter(1)


def reduce_count_brains(acc, b):
    acc[b.portal_type] += 1
    return acc


def get_qa(catalog, brain):
    path = brain.getPath()
    return catalog.unrestrictedSearchResults(
        portal_type=['Comment', 'CommentAnswer'],
        path=path
    )


def current_status(brain):
    status = brain['observation_status']
    return QUESTION_WORKFLOW_MAP.get(status, status)


def count_answers(len_q, len_a, obs_status):
    wf_is_msc = obs_status == QUESTION_WORKFLOW_MAP['MSC']
    answer_not_submitted = wf_is_msc and len_a and len_q == len_a

    return len_a - 1 if answer_not_submitted else len_a


def count_questions(len_q, len_a, obs_status):
    wf_is_se_or_lr = obs_status in [
        QUESTION_WORKFLOW_MAP['SE'],
        QUESTION_WORKFLOW_MAP['LR']
    ]
    question_not_submitted = wf_is_se_or_lr and len_q and len_q > len_a

    return len_q - 1 if question_not_submitted else len_q


def description_flags(vocab, brain):
    value = brain['get_highlight']
    return [vocab.getTerm(v).title for v in value] if value else []


def ipcc_sector(brain):
    return brain['get_ghg_source_sectors'][0]


def review_sector(mapping, se):
    return COL_CAT__RS(mapping[se])


def author_name(brain):
    return brain['get_author_name'].title()


def sector_expert(ms_roles, country):
    return COL_SE__ROLES_MS(ms_roles[country])


def lead_reviewer(ms_roles, country):
    return COL_LR__ROLES_MS(ms_roles[country])


def extract_entry(catalog, timestamp, mappings, vocab_highlights, brain):
    qa = get_qa(catalog, brain)
    qa_count = reduce(reduce_count_brains, qa, defaultdict(int))

    ms_roles = mappings['ms_roles']
    review_sectors = mappings['review_sectors']

    country_code = brain['country']
    se = sector_expert(ms_roles, country_code)

    obs_status = brain['observation_status']

    len_a = qa_count['CommentAnswer']
    len_q = qa_count['Comment']

    return {
        'Current status': current_status(brain),
        'IPCC Sector': ipcc_sector(brain),
        'Review sector': review_sector(review_sectors, se),
        'Author': author_name(brain),
        'Questions answered': count_answers(len_q, len_a, obs_status),
        'Questions asked': count_questions(len_q, len_a, obs_status),
        'Sector expert': se,
        'Lead reviewer': lead_reviewer(ms_roles, country_code),
        'Timestamp': timestamp,
        'Country': brain['country_value'],
        'ID': brain['id'],
        'Description flags': description_flags(vocab_highlights, brain)

    }


def validate_token(request):
    return request.get('tableau_token') == TOKEN if TOKEN else False


def sheet_ms_roles(sheet):
    rows = islice(sheet.rows, 1, None)  # skip header
    return {
        COL_MS__ROLES_MS(values).lower(): values
        for values in (tuple(cell.value for cell in row) for row in rows)
    }


def sheet_review_sectors(sheet):
    rows = islice(sheet.rows, 1, None)  # skip header
    return {
        COL_SE__RS(values): values
        for values in (tuple(cell.value for cell in row) for row in rows)
    }


def values_from_xls(xls):
    sheets = xls.worksheets

    return dict(
        ms_roles=sheet_ms_roles(SHEET_MS_ROLES(sheets)),
        review_sectors=sheet_review_sectors(SHEET_RS(sheets))
    )


class TableauView(BrowserView):
    def __call__(self):
        data = dict(status=401)
        request = self.request

        if validate_token(request):
            catalog = getToolByName(self.context, 'portal_catalog')
            timestamp = datetime.now().isoformat()
            folder = self.context

            vocab_highlights = getUtility(
                IVocabularyFactory,
                name='emrt.necd.content.highlight')(folder)

            xls_file = load_workbook(
                folder.xls_mappings.open(), read_only=True)

            mappings = values_from_xls(xls_file)

            entry = partial(
                extract_entry,
                catalog, timestamp, mappings, vocab_highlights)

            brains = catalog.unrestrictedSearchResults(
                portal_type=['Observation'],
                path='/'.join(folder.getPhysicalPath())
            )

            data = map(entry, brains)
        else:
            request.RESPONSE.setStatus(401)

        return jsonify(request, data)
