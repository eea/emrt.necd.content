from StringIO import StringIO
from functools import partial
from operator import attrgetter

from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory

from Products.Five.browser import BrowserView

from openpyxl import Workbook
from openpyxl.styles import Alignment


XLS_SAMPLE_HEADER = [
    'Observation description', 'Country', 'NFR Code',
    'Inventory Year', 'Pollutants', 'Review Year', 'Parameter'
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

        countries = map(get_title, country_voc)
        pollutants = '\n'.join(map(get_title, pollutants_voc))
        parameter = '\n'.join(map(get_title, parameter_voc))

        sheet.append(XLS_SAMPLE_HEADER)
        for country in countries:
            row = [DESC, country, NFR_CODE, INVENTORY_YEAR, pollutants,
                   REVIEW_YEAR, parameter]
            sheet.append(row)

    def __call__(self):
        wb = Workbook()
        sheet = wb.create_sheet('Observation', 0)

        self.populate_cells(sheet)

        # wrap text for multi line cells
        for row in sheet.iter_rows():
            for cell in row:
                cell.alignment = Alignment(wrap_text=True)

        # set cell max width
        for column_cells in sheet.columns:
            length = max(len(str(cell.value)) for cell in column_cells)
            sheet.column_dimensions[column_cells[0].column].width = length

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
