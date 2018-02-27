from emrt.necd.content.observation import IObservation
from functools import partial
from itertools import islice
from operator import itemgetter
from plone import api
from Products.Five.browser import BrowserView

from Products.CMFPlone.utils import safe_unicode


from Products.statusmessages.interfaces import IStatusMessage
from emrt.necd.content import MessageFactory as _

import openpyxl


UNREQUIERED_FIELDS = ['fuel', 'ms_key_category', 'highlight',
                      'closing_comments', 'closing_deny_comments']

UNCOMPLETED_ERR = 'The observation you uploaded seems to be a bit off. Please' \
                  ' fill all the fields as shown in the import file sample. '


def _read_row(idx, row):
    val = itemgetter(idx)(row).value

    if not val:
        return ''

    if isinstance(val, (int, long)):
        val = safe_unicode(str(val))
    return val.strip()

def _multi_rows(row):
    return tuple(val.strip() for val in row.split('\n'))


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
        return _multi_rows(COL_POLLUTANTS(self.row))

    @property
    def review_year(self):
        return int(COL_REVIEW_YEAR(self.row))

    @property
    def parameter(self):
        return _multi_rows(COL_PARAMS(self.row))

    def get_fields(self):
        return {name: getattr(self, name)
                for name in IObservation
                if name not in UNREQUIERED_FIELDS
                }


def _create_observation(entry, context, request, portal_type):

    if '' in entry.get_fields().values():
        status = IStatusMessage(request)
        msg = _(safe_unicode(UNCOMPLETED_ERR))
        status.addStatusMessage(msg, "error")
        url = context.absolute_url() + '/observation_import_form'
        return request.response.redirect(url)

    content = api.content.create(
        context,
        type=portal_type,
        title = getattr(entry, 'title'),
        **entry.get_fields()
    )
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

        # skip the document header
        valid_rows = tuple(islice(sheet, sheet.max_row))[1:]


        entries = map(Entry, valid_rows)

        for entry in entries:
            _create_observation(entry, self.context, self.request, PORTAL_TYPE)

        return 'DONE!'