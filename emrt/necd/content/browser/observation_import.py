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

import logging
import openpyxl


def _read_row(idx, row):
    return itemgetter(idx)(row).value.strip()


COL_TITLE = partial(_read_row, 0)
COL_POLLUTANTS = partial(_read_row, 1)
COL_PARAMS = partial(_read_row, 2)
COL_DESC = "Bla bla bla"


PORTAL_TYPE = 'Observation'


class Entry(object):
    def __init__(self, row):
        self.row = row

    @property
    def title(self):
        return True

    @property
    def pollutants(self):
        # pvoc = api.portal.get_tool('portal_vocabularies')
        # voc = pvoc.getVocabularyByName('pollutants')

        return ['PAHs']
        # return COL_POLLUTANTS(self.row)

    @property
    def parameter(self):
        return COL_PARAMS(self.row)

    @property
    def text(self):
        return COL_DESC

    @property
    def closing_deny_comments(self):
        pass

    @property
    def country(self):
        return 'at'

    @property
    def fuel(self):
        pass

    @property
    def nfr_code(self):
        return '1A1'

    @property
    def review_year(self):
        return 2018

    @property
    def year(self):
        return 2017

    @property
    def ms_key_category(self):
        pass

    @property
    def highlight(self):
        pass

    @property
    def closing_comments(self):
        pass

    def get_fields(self):
        return {name: getattr(self, name) for name in IObservation}

def _log_created(portal_type, content):
    # LOG.info(
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

from Products.statusmessages.interfaces import IStatusMessage
from emrt.necd.content import MessageFactory as _
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


