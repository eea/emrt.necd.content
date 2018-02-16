from functools import partial
from operator import itemgetter
from Products.Five.browser import BrowserView

import openpyxl


def _read_row(idx, row):
    return itemgetter(idx)(row).value.strip()


COL_TITLE = partial(_read_row, 3)


class ObservationXLSImport(BrowserView):


    def do_import(self):
        pass


class Observation(object):
    def __init__(self, title):
        self.title = title


class Entry(object):
    def __init__(self, row):
        self.row = row

    @property
    def title(self):
        return COL_TITLE(self.row)

    def get_query(self):
        def _and_query(value):
            return dict(query=value, operator='and')

        return dict(
            title=self.title,
            
            ),



