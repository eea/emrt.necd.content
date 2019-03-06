import os
import simplejson as json
from StringIO import StringIO

from gzip import GzipFile
from datetime import datetime

from collections import defaultdict
from collections import Counter

from operator import itemgetter
from itertools import islice
from itertools import chain

from functools import partial
from functools import reduce

from zope.component.hooks import getSite
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory

from ZODB.blob import Blob

from Products.Five import BrowserView

from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from openpyxl import load_workbook

from emrt.necd.content.utils import jsonify
from emrt.necd.content.reviewfolder import QUESTION_WORKFLOW_MAP


TOKEN_VIEW = os.environ.get("TABLEAU_TOKEN")
TOKEN_SNAP = os.environ.get("TABLEAU_TOKEN_SNAPSHOT")

HISTORICAL_ATTR_NAME = '__tableau_historical_store__'


SHEET_MS_ROLES = itemgetter(0)
SHEET_RS = itemgetter(1)

COL_MS__ROLES_MS = itemgetter(0)
COL_LR__ROLES_MS = itemgetter(1)
COL_SE__ROLES_MS = itemgetter(2)

COL_SE__RS = itemgetter(0)
COL_CAT__RS = itemgetter(1)


try:
    from flatten_json import flatten as do_flatten
except ImportError:
    def do_flatten(json_str):
        return json.dumps(list(chain(*json.loads(json_str))))


def insert_snapshot(data, snapshot):
    # type: (str, list) -> str
    return data[:1] + json.dumps(snapshot) + ',' + data[1:]


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
    return list({COL_CAT__RS(mapping[s]) for s in se})


def author_name(brain):
    return brain['get_author_name'].title()


def sector_expert(ms_roles, country):
    return list(set(map(COL_SE__ROLES_MS, ms_roles[country])))


def lead_reviewer(ms_roles, country):
    return list(set(map(COL_LR__ROLES_MS, ms_roles[country])))


def extract_entry(qa, timestamp, mappings, vocab_highlights, brain):
    b_id = brain['id']
    ms_roles = mappings['ms_roles']
    review_sectors = mappings['review_sectors']

    country_code = brain['country']
    se = sector_expert(ms_roles, country_code)

    obs_status = brain['observation_status']

    len_a = qa['CommentAnswer'][b_id]
    len_q = qa['Comment'][b_id]

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
        'ID': b_id,
        'URL': brain.getURL(),
        'Description flags': description_flags(vocab_highlights, brain)

    }


def validate_token(request, token=TOKEN_VIEW):
    return request.get('tableau_token') == token if token else False


def sheet_ms_roles(sheet):
    rows = islice(sheet.rows, 1, None)  # skip header

    result = defaultdict(tuple)

    for row in rows:
        values = tuple(c.value for c in row)
        result[COL_MS__ROLES_MS(values).lower()] += (values, )

    return dict(result)


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


def get_snapshot(context):
    catalog = getToolByName(context, 'portal_catalog')
    timestamp = datetime.now().isoformat()

    # Grab QA information. It's much faster to fetch the data
    # directly from the indexes than it is to query for it.
    idx_type = catalog._catalog.indexes['portal_type']._index
    idx_path = catalog._catalog.indexes['path']._unindex

    b_comment = idx_type['Comment']
    b_comment_answer = idx_type['CommentAnswer']

    p_comment = [idx_path[x] for x in b_comment]
    p_comment_answer = [idx_path[x] for x in b_comment_answer]

    qa = dict(
        Comment=Counter(p.split('/')[3] for p in p_comment),
        CommentAnswer=Counter(p.split('/')[3] for p in p_comment_answer),
    )

    vocab_highlights = getUtility(
        IVocabularyFactory,
        name='emrt.necd.content.highlight')(context)

    xls_file = load_workbook(
        context.xls_mappings.open(), read_only=True)

    mappings = values_from_xls(xls_file)

    entry = partial(
        extract_entry,
        qa, timestamp, mappings, vocab_highlights)

    brains = catalog.unrestrictedSearchResults(
        portal_type=['Observation'],
        path='/'.join(context.getPhysicalPath())
    )

    return map(entry, brains)


def write_historical_data(context, content):
    target = context.aq_inner.aq_self

    # get and clear existing data
    blob = getattr(target, HISTORICAL_ATTR_NAME).open('r+')
    blob.seek(0)
    blob.truncate()

    # gzip
    gzip = GzipFile(fileobj=blob, mode='w')
    gzip.write(content)

    gzip.close()

    # get gzipped data
    blob.seek(0)
    compressed = blob.read()

    blob.close()

    # return the compressed and uncompressed sizes
    return len(compressed), len(content)


def get_historical_data(context):
    """ Returns the raw string, since json.load is much too slow. """
    target = context.aq_inner.aq_self

    # create empty Blob, if missing
    if not hasattr(target, HISTORICAL_ATTR_NAME):
        setattr(target, HISTORICAL_ATTR_NAME, Blob())
        write_historical_data(context, '[]')

    # gunzip data
    blob = getattr(target, HISTORICAL_ATTR_NAME).open('r')
    gzip = GzipFile(fileobj=blob, mode='r')

    data = gzip.read()

    gzip.close()
    blob.close()

    return data


class TableauView(BrowserView):
    def __call__(self):
        data = dict(status=401)
        request = self.request

        if validate_token(request):
            data = get_snapshot(self.context)
        else:
            request.RESPONSE.setStatus(401)

        return jsonify(request, data, sort_keys=False, indent=None)


class TableauHistoricalView(BrowserView):
    def __call__(self, flatten=False):
        data = dict(status=401)
        request = self.request

        if validate_token(request):
            context = self.context

            data = get_historical_data(context)
            snapshot = get_snapshot(context)
            data = insert_snapshot(data, snapshot)

        else:
            request.RESPONSE.setStatus(401)

        if flatten:
            data = do_flatten(data)

        header = request.RESPONSE.setHeader
        header("Content-Type", "application/json")

        return data


class TableauCreateSnapshotView(BrowserView):
    def __call__(self):
        data = dict(status=401)
        request = self.request

        if validate_token(request, TOKEN_SNAP):
            context = self.context
            historical = get_historical_data(context)
            historical = insert_snapshot(historical, get_snapshot(context))
            compressed, content = write_historical_data(
                context, historical)
            data['size'] = compressed
            data['deflated'] = content
            data['status'] = 200
        else:
            request.RESPONSE.setStatus(401)

        return jsonify(request, data, sort_keys=False, indent=None)


class ConnectorView(BrowserView):

    index = ViewPageTemplateFile('./templates/tableau_connector.pt')

    def __call__(self, historical=False):
        request = self.request

        # Make sure the response doesn't get cached in proxies.
        request.RESPONSE.setHeader('Surrogate-control', 'no-store')

        if validate_token(request):

            if historical:
                data = self.historical_data()
            else:
                data = self.data()

            return self.index(
                portal_url=getSite().absolute_url(),
                data=data
            )

        request.RESPONSE.setStatus(401)

    def data(self):
        return json.dumps(get_snapshot(self.context))

    def historical_data(self):
        context = self.context
        data = get_historical_data(context)
        data = insert_snapshot(data, get_snapshot(context))
        return do_flatten(data)
