# -*- coding: utf-8 -*-
import os
from plone import api

import logging

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone.app.textfield import RichTextValue
from plone.app.discussion.interfaces import IConversation

from collective.exportimport import import_other


logger = logging.getLogger(__name__)

class ImportDiscussion(import_other.ImportDiscussion):
    """Import discussions / comments"""

    index = ViewPageTemplateFile(
        "templates/import_discussion.pt",
        _prefix=os.path.dirname(import_other.__file__),
    )

    def import_data(self, data):
        results = 0
        for conversation_data in data:
            obj = api.content.get(UID=conversation_data["uuid"])
            if not obj:
                continue
            updated = 0
            conversation = IConversation(obj)

            for item in conversation_data["conversation"]["items"]:
                needs_update = (
                    isinstance(item["text"], dict) 
                    and item["text"].get("mime-type") == "text/html"
                )

                if needs_update:
                    comment_id = int(item["comment_id"])
                    comment = conversation._comments.get(comment_id)
                    if comment:
                        comment.text = RichTextValue(
                            item["text"], "text/html", "text/x-html-safe"
                        )
                        updated += 1
                    else:
                        warn_msg = (
                            "Comment with id %s not found in %s. "
                            "Make sure to run @@import_discussion before "
                            "running @@necd_import_discussion!"
                        )
                        logger.warning(
                            warn_msg,
                            comment_id,
                            obj.absolute_url(),
                        )
            if updated:
                logger.info(
                    "Updated %s comments to %s", 
                    updated, 
                    obj.absolute_url(),
                )
            results += updated

        return results