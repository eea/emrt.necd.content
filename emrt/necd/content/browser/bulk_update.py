from logging import getLogger
from functools import partial

from zope.component.hooks import getSite


from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from Products.CMFCore.utils import getToolByName
from Products.statusmessages.interfaces import IStatusMessage

import openpyxl

from emrt.necd.content.browser.xls_utils import get_valid_sheet_rows
from emrt.necd.content.browser.xls_utils import clean_value

LOG = getLogger('emrt.necd.content.bulk_update')


def _read_col(row, nr):
    try:
        val = clean_value(row[nr].value)
    except IndexError:
        val = u''
    return val.strip() if val else u''


def _obj_from_url(context, site_url, url):
    traversable = str(url.split(site_url)[-1][1:])
    return context.unrestrictedTraverse(traversable)


def replace_conclusion_text(obj, text):
    conclusion = obj.get_conclusion()
    if text and conclusion:
        conclusion.text = text

def replace_description_text(obj, text):
    if text:
        obj.text = text


class BulkUpdateView(BrowserView):

    index = ViewPageTemplateFile('templates/bulk_update.pt')

    def __call__(self):
        return self.index()

    def start(self, xls):
        portal = getSite()
        wb = openpyxl.load_workbook(xls, read_only=True, data_only=True)
        sheet = wb.worksheets[0]

        valid_rows = get_valid_sheet_rows(sheet)

        context = self.context
        site_url = portal.absolute_url()
        obj_from_url = partial(_obj_from_url, context, site_url)
        catalog = getToolByName(portal, 'portal_catalog')

        for row in valid_rows:
            target = _read_col(row, 0)
            conclusion_text = _read_col(row, 1)
            description_text = _read_col(row, 2)
            ob = obj_from_url(target)
            replace_conclusion_text(ob, conclusion_text)
            replace_description_text(ob, description_text)
            catalog.reindexObject(ob, idxs=["SearchableText"])

        if len(valid_rows) > 0:
            (IStatusMessage(self.request)
                .add('Bulk update successful!', type='info'))
        else:
            (IStatusMessage(self.request)
                .add('No data provided!', type='warn'))
        self.request.RESPONSE.redirect(context.absolute_url())
