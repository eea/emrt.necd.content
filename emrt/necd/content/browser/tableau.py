import os
from datetime import datetime

from collections import defaultdict
from functools import partial
from functools import reduce

from Products.Five import BrowserView

from Products.CMFCore.utils import getToolByName

from emrt.necd.content.utils import jsonify
from emrt.necd.content.reviewfolder import QUESTION_WORKFLOW_MAP


TOKEN = os.environ.get("TABLEAU_TOKEN")


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


def ipcc_sector(brain):
    # TODO: request a mapping for the sector
    return brain['get_ghg_source_sectors'][0]


def review_sector(brain):
    return brain['get_ghg_source_sectors'].split()[0]


def author_name(brain):
    return brain['get_author_name'].title()


def extract_entry(catalog, timestamp, brain):
    qa = get_qa(catalog, brain)
    qa_count = reduce(reduce_count_brains, qa, defaultdict(int))

    return {
        'Current status': current_status(brain),
        'IPCC Sector': ipcc_sector(brain),
        'Review sector': review_sector(brain),
        'Author': author_name(brain),
        'Questions answered': qa_count['CommentAnswer'],
        'Questions asked': qa_count['Comment'],
        'Timestamp': timestamp,
    }


def validate_token(request):
    return request.get('tableau_token') == TOKEN if TOKEN else False


class TableauView(BrowserView):
    def __call__(self):
        data = dict(status=401)
        request = self.request

        if validate_token(request):
            catalog = getToolByName(self.context, 'portal_catalog')
            timestamp = datetime.now().isoformat()
            entry = partial(extract_entry, catalog, timestamp)
            folder = self.context

            brains = catalog.unrestrictedSearchResults(
                portal_type=['Observation'],
                path='/'.join(folder.getPhysicalPath())
            )

            data = map(entry, brains)
        else:
            request.RESPONSE.setStatus(401)

        return jsonify(request, data)
