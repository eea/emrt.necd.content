from functools import partial
from itertools import takewhile
from operator import itemgetter
from plone import api
from Products.Five.browser import BrowserView
from zope import component
from z3c.relationfield import RelationValue

import logging
import openpyxl

from emrt.necd.content.vocabularies import Parameter

# LOG =


def _read_row(idx, row):
    return itemgetter(idx)(row).value.strip()


COL_TITLE = partial(_read_row, 0)
COL_POLLUTANTS = partial(_read_row, 1)
COL_PARAMS = partial(_read_row, 2)


PORTAL_TYPE = 'Observation'


class Entry(object):
    def __init__(self, row):
        self.row = row

    @property
    def title(self):
        return COL_TITLE(self.row)

    @property
    def pollutants(self):
        return COL_POLLUTANTS(self.row)

    @property
    def parameter(self):
        return COL_PARAMS(self.row)

def _log_created(portal_type, title, content):
    # LOG.info(
    print(
        u'Created new %s for %s: %s!',
        portal_type, title, content.absolute_url(1))


def _create_observation(context, portal_type, title, pollutants, parameter):

    content = api.content.create(
        context,
        type=portal_type,
        title=title,
        pollutants=pollutants,
        parameter=parameter,
    )
    _log_created(portal_type, title, content)
    return content

class ObservationXLSImport(BrowserView):


    def do_import(self):
        xls_file = self.request.get('xls_file', None)
        wb = openpyxl.load_workbook(xls_file, read_only=True)
        sheet = wb.worksheets[0]

        entries = map(Entry, sheet.rows)

        for entry in entries:
            _create_observation(self.context, PORTAL_TYPE, entry.title, entry.pollutants, entry.parameter)

        return 'DONE!'


