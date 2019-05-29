from logging import getLogger

from Products.CMFCore.utils import getToolByName

import plone.api as api

from emrt.necd.content.upgrades import portal_workflow as upw
from emrt.necd.content.browser.carryover import clear_and_grant_roles


LOG = getLogger(__name__)


def fix_permissions(context, catalog):
    wft = getToolByName(context, 'portal_workflow')
    type_mapping = upw.get_workflow_type_mapping(wft)

    queries = [
        dict(
            portal_type='Observation',
            review_state=['draft', 'pending'],
            reindex_self_only=True,
        ),
        # Reindex old content from 2.3.6 migration.
        # Needed because of fixed bug in upw which
        # didn't reindex the correct objects.
        dict(
            portal_type='Comment',
            review_state='initial',
            reindex_self_only=True,
        ),
    ]

    upw.upgrade(wft, catalog, type_mapping, queries)


def run(context):
    catalog = getToolByName(context, 'portal_catalog')
    portal = api.portal.get()

    fix_permissions(context, catalog)
