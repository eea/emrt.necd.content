from Products.Five.browser import BrowserView
from StringIO import StringIO

from openpyxl import Workbook
from openpyxl.styles.borders import Border, Side

XLS_SAMPLE_HEADER = ['Observation description', 'Country', 'NFR Code',
                     'Inventory Year', 'Pollutants', 'Review Year', 'Parameter']


class GetSampleXLS(BrowserView):

    def set_border(self, sheet, max_row, max_col):

        medium_border = Border(left=Side(style='medium'),
                               right=Side(style='medium'),
                               top=Side(style='medium'),
                               bottom=Side(style='medium'))

        for row in range(1,max_row+1):
            for col in range(1,max_col+1):
                sheet.cell(row=row, column=col).border = medium_border


    def populate_cells(self, sheet):

        sheet.append(XLS_SAMPLE_HEADER)

        sheet['A2'] = 'Here comes the short description of the observation'
        sheet['C2'] = '1A1'
        sheet['D2'] = '2017'
        sheet['F2'] = '2018'

        self.set_border(sheet, sheet.max_row, sheet.max_column)


    def __call__(self):
        wb = Workbook()
        sheet = wb.create_sheet('Observation', 0)

        self.populate_cells(sheet)

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
