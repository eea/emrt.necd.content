from emrt.necd.content import MessageFactory as _
from emrt.necd.content.vocabularies import get_registry_interface_field_data
from emrt.necd.content.vocabularies import INECDVocabularies
from functools import partial
from itertools import islice
from itertools import chain
from operator import itemgetter
from plone import api
from Products.CMFPlone.utils import safe_unicode
from Products.Five.browser import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
import Acquisition
import openpyxl


UNUSED_FIELDS = ['closing_comments', 'closing_deny_comments']

UNCOMPLETED_ERR = u'The observation on row no. {} seems to be a bit off. ' \
                  u'Please fill all the fields as shown in the import file' \
                  u' sample. '

WRONG_DATA_ERR = u'The information you entered in the {} section ' \
                 u'of row no. {} is not correct. Please consult the columns' \
                 u' in the sample xls file to see the correct set of data.' \

DONE_MSG = u'Successfully imported {} observations!'


def _read_row(idx, row):
    val = itemgetter(idx)(row).value

    if not val:
        return ''

    if isinstance(val, (int, long)):
        val = safe_unicode(str(val))
    return val.strip()

import re
def _multi_rows(row):
    splitted = re.split(r'[,\n]\s*', row)
    return tuple(val.strip() for val in splitted)


def get_constants(context):
    XLS_COLS = {}
    XLS_COLS['text'] = partial(_read_row, 0)
    XLS_COLS['country'] = partial(_read_row, 1)
    XLS_COLS['nfr_code'] = partial(_read_row, 2)
    idx = 3
    projection_cols = ['nfr_code_inventory', 'year', 'reference_year',
                       'pollutants', 'scenario', 'review_year',
                       'activity_data_type', 'activity_data', 'ms_key_category',
                       'parameter', 'highlight']
    inventory_cols = ['year', 'pollutants', 'review_year', 'fuel',
                      'ms_key_category', 'parameter', 'highlight']

    if context == 'projection':
        for col in projection_cols:
            XLS_COLS[col] = partial(_read_row, idx)
            idx+=1
    else:
        for col in inventory_cols:
            XLS_COLS[col] = partial(_read_row, idx)
            idx += 1

    return XLS_COLS


def get_registry_voc(field):
    return get_registry_interface_field_data(INECDVocabularies, field)


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

    def __init__(self, row, constants):
        self.row = row
        self.constants = constants

    @property
    def title(self):
        return True

    @property
    def text(self):
        return self.constants['text'](self.row)

    @property
    def country(self):
        country_voc = get_vocabulary('eea_member_states')
        cell_value = self.constants['country'](self.row)
        return find_dict_key(country_voc, cell_value)

    @property
    def nfr_code(self):
        return self.constants['nfr_code'](self.row)

    @property
    def nfr_code_inventory(self):
        nfr = self.constants['nfr_code_inventory'](self.row)
        return nfr if nfr != '' else None

    @property
    def year(self):
        # Projection year
        if len(self.constants) > 10:
            years = _multi_rows(self.constants['year'](self.row))
            if years == ('',):
                return ''
            proj_years = [u'2020', u'2025', u'2030', u'2040', u'2050']
            is_correct = bool(set(years) & set(proj_years))
            return u','.join(years) if is_correct else False

        # Inventory year
        return self.constants['year'](self.row)

    @property
    def reference_year(self):
        return int(self.constants['reference_year'](self.row))

    @property
    def pollutants(self):
        if len(self.constants) >10:
            pollutants_voc = get_registry_voc('projection_pollutants')
        else:
            pollutants_voc = get_vocabulary('pollutants')
        cell_value = _multi_rows(self.constants['pollutants'](self.row))
        keys = [find_dict_key(pollutants_voc, key) for key in cell_value]
        if False in keys:
            return False
        return keys

    @property
    def scenario(self):
        scenario_voc = get_vocabulary('scenario_type')
        cell_value = _multi_rows(self.constants['scenario'](self.row))
        if cell_value == ('',):
            return None
        keys = [find_dict_key(scenario_voc, key) for key in cell_value]
        if False in keys:
            return False
        return keys

    @property
    def review_year(self):
        return int(self.constants['review_year'](self.row))

    @property
    def activity_data_type(self):
        activity_voc = get_registry_voc('activity_data').keys()
        cell_value = self.constants['activity_data_type'](self.row)
        if cell_value == '':
            return None
        if cell_value not in activity_voc:
            return False
        return cell_value

    @property
    def activity_data(self):
        activity_voc = get_registry_voc('activity_data').values()
        cell_value = _multi_rows(self.constants['activity_data'](self.row))
        if cell_value == ('',):
            return None
        elif not self.activity_data_type:
            return False

        keys = [key if key in chain(*activity_voc)
                    else False for key in cell_value]
        if False in keys:
            return False
        else:
            activity_data_registry = get_registry_interface_field_data(
                INECDVocabularies, 'activity_data')
            if not all(activity in activity_data_registry[self.activity_data_type]
                       for activity in keys):
                return False
        return keys

    @property
    def fuel(self):
        fuel_voc = get_vocabulary('fuel')
        cell_value = self.constants['fuel'](self.row)
        if cell_value != '':
            return find_dict_key(fuel_voc, cell_value)
        #This field can be none because it's not manadatory
        return None

    @property
    def ms_key_category(self):
        cell_value = self.constants['ms_key_category'](self.row).title()

        if cell_value == 'True':
            return cell_value
        elif cell_value == '':
            #openpyxl takes False cell values as empty strings so it is easier
            #to assume that an empty cell of the MS Key Category column
            # evaluates to false
            return 'False'

        # For the incorrect data check
        return False

    @property
    def parameter(self):
        parameter_voc = get_vocabulary('parameter')
        cell_value = _multi_rows(self.constants['parameter'](self.row))
        keys = [find_dict_key(parameter_voc, key) for key in cell_value]
        if False in keys:
            return False
        return keys

    @property
    def highlight(self):
        if len(self.constants) > 10:
            highlight_voc = get_vocabulary('highlight_projection')
        else:
            highlight_voc = get_vocabulary('highlight')
        col_desc_flags = self.constants['highlight'](self.row)
        if col_desc_flags != '':
            cell_value = _multi_rows(col_desc_flags)
            keys = [find_dict_key(highlight_voc, key) for key in cell_value]
            if False in keys:
                return False
            else:
                return keys
        else:
            # This field can be none because it's not manadatory
            return None


    def get_fields(self):
        # Moving activity_data_type field first to validate activity_data values
        fields = self.constants.keys()
        fields.insert(0, fields.pop(fields.index('activity_data_type')))

        return {
            name: getattr(self, name)
            for name in fields
            if name not in UNUSED_FIELDS
        }


def _create_observation(entry, context, request, portal_type, obj):
    obj.row_nr += 1

    fields = entry.get_fields()

    if '' in fields.values():
        return error_status_message(
            context, request, UNCOMPLETED_ERR.format(obj.row_nr - 1)
        )

    elif False in fields.values():
        key = find_dict_key(fields, False)
        if key == 'highlight':
            key = 'description flags'
        msg = WRONG_DATA_ERR.format(key, obj.row_nr - 1)
        return error_status_message(context, request, msg)

    #Values must be boolean
    if fields['ms_key_category'] == 'True':
        fields['ms_key_category'] = True
    else:
        fields['ms_key_category'] = False

    content = api.content.create(
        context,
        type=portal_type,
        title = getattr(entry, 'title'),
        **fields
    )

    obj.num_entries +=1
    return content


class ObservationXLSImport(BrowserView):

    num_entries = 0
    row_nr = 2

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

        wb = openpyxl.load_workbook(xls_file, read_only=True, data_only=True)
        sheet = wb.worksheets[0]

        max = self.valid_rows_index(sheet)

        # skip the document header
        valid_rows = islice(sheet, 1, max-1)

        entries = []
        for row in valid_rows:
            entries.append(Entry(row, get_constants(self.context.type)))

        for entry in entries:
            _create_observation(
                entry, self.context, self.request, PORTAL_TYPE, self
            )

        if self.num_entries > 0:
            status = IStatusMessage(self.request)
            status.addStatusMessage(_(DONE_MSG.format(self.num_entries)))

        return self.request.response.redirect(self.context.absolute_url())