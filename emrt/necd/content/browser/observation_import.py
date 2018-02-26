from emrt.necd.content.observation import IObservation
from functools import partial
from itertools import takewhile
from operator import itemgetter
from plone import api
from Products.Five.browser import BrowserView
from zope import component
from z3c.relationfield import RelationValue

from Products.CMFPlone.utils import safe_unicode
from emrt.necd.content.nfr_code_matching import get_category_ldap_from_nfr_code

from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory

from Products.statusmessages.interfaces import IStatusMessage
from emrt.necd.content import MessageFactory as _

import logging
import openpyxl


def _read_row(idx, row):
    val = itemgetter(idx)(row).value

    if isinstance(val, (int, long)):
        val = safe_unicode(str(val))
    return val.strip()


COL_DESC = partial(_read_row, 0)
COL_COUNTRY = partial(_read_row, 1)
COL_NFR = partial(_read_row, 2)
COL_YEAR = partial(_read_row, 3)
COL_POLLUTANTS = partial(_read_row, 4)
COL_REVIEW_YEAR = partial(_read_row, 5)
COL_PARAMS = partial(_read_row, 6)


PORTAL_TYPE = 'Observation'


class Entry(object):
    def __init__(self, row):
        self.row = row

    @property
    def title(self):
        return True

    @property
    def text(self):
        return COL_DESC(self.row)

    @property
    def country(self):
        return COL_COUNTRY(self.row)

    @property
    def nfr_code(self):
        return COL_NFR(self.row)

    @property
    def year(self):
        return COL_YEAR(self.row)

    @property
    def pollutants(self):
        return [COL_POLLUTANTS(self.row)]

    @property
    def review_year(self):
        return int(COL_REVIEW_YEAR(self.row))

    @property
    def fuel(self):
        pass

    @property
    def ms_key_category(self):
        pass

    @property
    def parameter(self):
        return [COL_PARAMS(self.row)]

    @property
    def highlight(self):
        pass

    @property
    def closing_comments(self):
        pass

    @property
    def closing_deny_comments(self):
        pass

    def get_fields(self):
        return {name: getattr(self, name) for name in IObservation}

def _log_created(portal_type, content):

    print(
        u'Created new %s for %s: %s!',
        portal_type, content.absolute_url(1))


def _create_observation(entry, context, portal_type):

    content = api.content.create(
        context,
        type=portal_type,
        title = getattr(entry, 'title'),
        **entry.get_fields()
    )
    _log_created(portal_type, content)
    return content


class ObservationXLSImport(BrowserView):


    def do_import(self):
        xls_file = self.request.get('xls_file', None)

        if xls_file.filename == '':
            status = IStatusMessage(self.request)
            msg = _(u'Please upload a xls file before importing!')
            status.addStatusMessage(msg, "error")
            url = self.context.absolute_url() + '/observation_import_form'
            return self.request.response.redirect(url)

        wb = openpyxl.load_workbook(xls_file, read_only=True)
        sheet = wb.worksheets[0]

        entries = map(Entry, sheet.rows)

        for entry in entries:
            _create_observation(entry, self.context, PORTAL_TYPE)

        return 'DONE!'


