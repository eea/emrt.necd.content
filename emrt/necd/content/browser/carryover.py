from logging import getLogger
from itertools import takewhile
from functools import partial

from zope.component.hooks import getSite

from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from Products.CMFCore.utils import getToolByName

import openpyxl


LOG = getLogger('emrt.necd.content.carryover')


def _read_col(row, nr):
    return row[nr].value.strip()


def _copy_obj(target, ob, new_id=None):
    orig_ob = ob
    ob_id = new_id or orig_ob.getId()
    ob = ob._getCopy(target)
    ob._setId(ob_id)
    target._setObject(ob_id, ob)
    return target[ob_id]


def _copy_and_flag(context, obj, new_id=None):
    _, _, year, index = (new_id or obj.getId()).split('-')
    ob = _copy_obj(context, obj, new_id=new_id)
    ob.carryover_from = year

    LOG.info(
        'Copied %s -> %s',
        obj.absolute_url(1),
        ob.absolute_url(1),
    )

    return ob


def _obj_from_url(context, site_url, url):
    traversable = str(url.split(site_url)[-1][1:])
    return context.unrestrictedTraverse(traversable)


def prepend_qa(target, source):
    source_qa = source.get_question()
    target_qa = target.get_question()

    if source_qa and target_qa:
        for comment in source_qa.values():
            _copy_obj(target_qa, comment)
            target.notifyAdded(comment.getId())
        target_qa.orderObjects(key='creation_date')
    elif source_qa and not target_qa:
        _copy_obj(target, source_qa)


def copy_direct(context, rows):
    site_url = getSite().absolute_url()
    obj_from_url = partial(_obj_from_url, context, site_url)
    catalog = getToolByName(context, 'portal_catalog')

    for row in rows:
        source = _read_col(row, 0)
        obj = obj_from_url(source)
        ob = _copy_and_flag(context, obj)
        catalog.catalog_object(ob)


def copy_complex(context, rows):
    site_url = getSite().absolute_url()
    obj_from_url = partial(_obj_from_url, context, site_url)
    catalog = getToolByName(context, 'portal_catalog')

    for row in rows:
        source = _read_col(row, 0)
        older_source = _read_col(row, 1)

        obj = obj_from_url(source)
        older_obj = obj_from_url(older_source)

        ob = _copy_and_flag(context, obj, older_obj.getId())

        prepend_qa(ob, older_obj)
        catalog.catalog_object(ob)


class CarryOverView(BrowserView):

    index = ViewPageTemplateFile('templates/carryover.pt')

    def __call__(self):
        return self.index()

    def start(self, action, xls):
        wb = openpyxl.load_workbook(xls, read_only=True, data_only=True)
        sheet = wb.worksheets[0]

        # extract rows with values, skip first row (header)
        valid_rows = tuple(takewhile(
            lambda row: any(c.value for c in row), sheet.rows))[1:]

        if action == 'direct':
            copy_direct(self.context, valid_rows)
        elif action == 'complex':
            copy_complex(self.context, valid_rows)
