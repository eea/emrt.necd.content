from itertools import cycle
from functools import partial
from openpyxl import Workbook
from openpyxl.styles import Alignment
from operator import attrgetter
from Products.Five.browser import BrowserView
from StringIO import StringIO
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory


XLS_SAMPLE_HEADER = [
    'Observation description', 'Country', 'NFR Code',
    'Inventory Year', 'Pollutants', 'Review Year', 'Fuel', 'MS Key Category',
    'Parameter', 'Description Flags'
]

DESC = 'Description of the observation'
NFR_CODE = '1A1'
INVENTORY_YEAR = '2017'
REVIEW_YEAR = '2017'


def _get_vocabulary(context, name):
    factory = getUtility(IVocabularyFactory, name=name)
    return factory(context)


class GetSampleXLS(BrowserView):

    def populate_cells(self, sheet):

        get_vocabulary = partial(_get_vocabulary, self.context)
        get_title = attrgetter('title')

        country_voc = get_vocabulary('emrt.necd.content.eea_member_states')
        pollutants_voc = get_vocabulary('emrt.necd.content.pollutants')
        parameter_voc = get_vocabulary('emrt.necd.content.parameter')
        fuel_voc = get_vocabulary('emrt.necd.content.fuel')
        description_flags_voc = get_vocabulary('emrt.necd.content.highlight')

        countries = map(get_title, country_voc)
        # not a mandatory field, value can be none
        fuels = cycle(map(get_title, fuel_voc) + [None])
        ms_key_categ = cycle(['True', None])
        pollutants = '\n'.join(map(get_title, pollutants_voc))
        parameter = '\n'.join(map(get_title, parameter_voc))
        description_flags = cycle(['\n'.join(map(get_title, description_flags_voc)), None])

        sheet.append(XLS_SAMPLE_HEADER)
        for idx, country in enumerate(countries):
            # get a value based on the country index position
            fuel = next(fuels)
            ms_key_cat = next(ms_key_categ)
            desc_fl = next(description_flags)
            row = [DESC, country, NFR_CODE, INVENTORY_YEAR, pollutants,
                   REVIEW_YEAR, fuel, ms_key_cat, parameter, desc_fl]
            sheet.append(row)

    def __call__(self):
        wb = Workbook()
        sheet = wb.create_sheet('Observation', 0)

        self.populate_cells(sheet)

        # wrap text for multi line cells and set max width
        for column in sheet.columns:
            length = []

            for cell in column:
                if cell.value:
                    length.append(max(len(str(c.rstrip())) for c in cell.value.splitlines()))
                    cell.alignment = Alignment(wrap_text=True)

            sheet.column_dimensions[column[0].column].width = max(length)

        xls = StringIO()

        wb.save(xls)

        xls.seek(0)
        filename = 'observation_import_sample.xlsx'
        self.request.response.setHeader(
            'Content-type', 'application/vnd.ms-excel; charset=utf-8'
        )
        self.request.response.setHeader(
            'Content-Disposition', 'attachment; filename={0}'.format(filename)
        )
        return xls.read()
