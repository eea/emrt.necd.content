from Products.CMFCore.utils import getToolByName

from emrt.necd.content.upgrades import portal_workflow as upw


def run(context):
    catalog = getToolByName(context, 'portal_catalog')
    wft = getToolByName(context, 'portal_workflow')
    type_mapping = upw.get_workflow_type_mapping(wft)

    queries = [
        dict(
            portal_type='Comment',
            review_state='initial',
            reindex_self_only=True,
        ),
    ]

    upw.upgrade(wft, catalog, type_mapping, queries)
