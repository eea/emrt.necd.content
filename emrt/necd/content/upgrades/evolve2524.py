import logging
import transaction
import plone.api as api

from Products.CMFCore.utils import getToolByName
from emrt.necd.content.upgrades import portal_workflow as upw


logger = logging.getLogger(__name__)


IDX = "reply_comments_by_mse"


def upgrade(_):
    portal = api.portal.get()
    rf = ["2021", "2021-projection"]
    rf = ["test-reviewfolder"]
    for folder in [portal[f] for f in rf]:
        for idx, obj in enumerate(folder.objectValues(), start=1):
            if obj.portal_type == "Observation":
                if idx % 1 == 0:
                    transaction.savepoint(optimistic=True)
                logger.info("[%s] Reindexing %s...", idx, obj.absolute_url(1))
                obj.reindexObject(
                    idxs=[
                        "observation_already_replied",
                        "observation_sent_to_msc",
                        "observation_sent_to_mse",
                    ]
                )
    transaction.commit()
