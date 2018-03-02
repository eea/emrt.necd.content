from openpyxl import Workbook
from openpyxl.styles import Alignment
from plone import api
from Products.Five.browser import BrowserView
from StringIO import StringIO


XLS_SAMPLE_HEADER = ['Observation description', 'Country', 'NFR Code',
                     'Inventory Year', 'Pollutants', 'Review Year', 'Parameter']

DESC = 'Description of the observation'
NFR_CODE = '1A1'
INVENTORY_YEAR = '2017'
REVIEW_YEAR = '2017'


class GetSampleXLS(BrowserView):

    def populate_cells(self, sheet):

        sheet.append(XLS_SAMPLE_HEADER)

        pvoc = api.portal.get_tool('portal_vocabularies')
        country_voc = pvoc.getVocabularyByName('eea_member_states')
        pollutants_voc = pvoc.getVocabularyByName('pollutants')
        parameter_voc = pvoc.getVocabularyByName('parameter')

        countries = [term.title for term in country_voc.values()]
        pollutants = '\n'.join([term.title for term in pollutants_voc.values()])
        parameter = '\n'.join([term.title for term in parameter_voc.values()])

        for country in countries:
            row = [DESC, country, NFR_CODE, INVENTORY_YEAR, pollutants,
                   REVIEW_YEAR, parameter]
            sheet.append(row)

    def __call__(self):
        wb = Workbook()
        sheet = wb.create_sheet('Observation', 0)

        self.populate_cells(sheet)

        #wrap text for multi line cells
        for row in sheet.iter_rows():
            for cell in row:
                cell.alignment = Alignment(wrap_text=True)


        #set cell max width
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
