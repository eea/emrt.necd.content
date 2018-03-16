from emrt.necd.content import MessageFactory as _
from emrt.necd.content.observation import IObservation
from functools import partial
from itertools import islice
from operator import itemgetter
from plone import api
from Products.CMFPlone.utils import safe_unicode
from Products.Five.browser import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
import Acquisition
import openpyxl


UNUSED_FIELDS = ['highlight', 'closing_comments', 'closing_deny_comments']

UNCOMPLETED_ERR = u'The observation you uploaded seems to be a bit off. Please' \
                  u' fill all the fields as shown in the import file sample. '

WRONG_DATA_ERR = u'The information you entered in the {} section is not correct.' \
                 u' Please consult the columns in the sample xls file to see the ' \
                 u'correct set of data.'

NO_FILE_ERR = u'Please upload a xls file before importing!'

DONE_MSG = u'Successfully imported {} observations!'


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
COL_FUEL = partial(_read_row, 6)
COL_MS_KEY = partial(_read_row, 7)
COL_PARAMS = partial(_read_row, 8)

PORTAL_TYPE = 'Observation'

def get_vocabulary(name):
    portal_voc = api.portal.get_tool('portal_vocabularies')
    return portal_voc.getVocabularyByName(name)


def find_dict_key(vocabulary, value):
    for key, val in vocabulary.items():
        if isinstance(val, list):
            if value in val:
                return key
        elif isinstance(val, Acquisition.ImplicitAcquisitionWrapper):
            if val.title == value:
                return key
        elif val == value:
            return key

    return False


def error_status_message(context, request, message):
    status = IStatusMessage(request)
    status.addStatusMessage(_(message), "error")
    url = context.absolute_url() + '/observation_import_form'
    return request.response.redirect(url)


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
        country_voc = get_vocabulary('eea_member_states')
        cell_value = COL_COUNTRY(self.row)
        return find_dict_key(country_voc, cell_value)

    @property
    def nfr_code(self):
        return COL_NFR(self.row)

    @property
    def year(self):
        return COL_YEAR(self.row)

    @property
    def pollutants(self):
        pollutants_voc = get_vocabulary('pollutants')
        cell_value = _multi_rows(COL_POLLUTANTS(self.row))
        keys = [find_dict_key(pollutants_voc, key) for key in cell_value]
        if False in keys:
            return False
        return keys

    @property
    def review_year(self):
        return int(COL_REVIEW_YEAR(self.row))

    @property
    def fuel(self):
        fuel_voc = get_vocabulary('fuel')
        cell_value = COL_FUEL(self.row)
        if cell_value != '':
            return find_dict_key(fuel_voc, cell_value)

        #This field can be none because it's not manadatory
        return None

    @property
    def ms_key_category(self):
        cell_value = COL_MS_KEY(self.row).title()
        if cell_value in ['True', 'False']:
            return cell_value

        # For the incorrect data check
        return False

    @property
    def parameter(self):
        parameter_voc = get_vocabulary('parameter')
        cell_value = _multi_rows(COL_PARAMS(self.row))
        keys = [find_dict_key(parameter_voc, key) for key in cell_value]
        if False in keys:
            return False
        return keys

    def get_fields(self):
        return {name: getattr(self, name)
                for name in IObservation
                if name not in UNUSED_FIELDS
                }


def _create_observation(entry, context, request, portal_type):

    fields = entry.get_fields()

    if '' in fields.values():
        return error_status_message(context, request, UNCOMPLETED_ERR)

    elif False in fields.values():
        key = find_dict_key(fields, False)
        msg = WRONG_DATA_ERR.format(key)
        return error_status_message(context, request, msg)

    content = api.content.create(
        context,
        type=portal_type,
        title = getattr(entry, 'title'),
        **fields
    )
    return content


class ObservationXLSImport(BrowserView):

    def valid_rows_index(self, sheet):
        """There are some cases when deleted rows from an xls file are seen
        as empty rows and the importer tries to create an object with no data
        """
        idx = 1
        for row in sheet:
            if any(cell.value for cell in row):
                idx += 1
        return idx

    def do_import(self):
        xls_file = self.request.get('xls_file', None)

        if xls_file.filename == '':
            return error_status_message(self.context, self.request, NO_FILE_ERR)

        wb = openpyxl.load_workbook(xls_file, read_only=True)
        sheet = wb.worksheets[0]

        max = self.valid_rows_index(sheet)

        # skip the document header
        valid_rows = islice(sheet, 1, max-1)

        entries = map(Entry, valid_rows)

        num_entries = 0
        for entry in entries:
            _create_observation(entry, self.context, self.request, PORTAL_TYPE)
            num_entries += 1

        status = IStatusMessage(self.request)
        status.addStatusMessage(_(DONE_MSG.format(num_entries)))

        return self.request.response.redirect(self.context.absolute_url())