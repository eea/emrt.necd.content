# -*- coding: utf-8 -*-
import os
from plone import api

import logging

from urllib.parse import unquote
from urllib.parse import urlparse

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone.app.textfield import RichTextValue
from plone.app.discussion.interfaces import IConversation

from collective.exportimport import import_other

from collective.exportimport.import_other import PORTAL_PLACEHOLDER
from collective.exportimport.import_other import ZLogHandler

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
            parent_url = unquote(conversation_data["@id"])
            parent_path = urlparse(parent_url).path
            obj = api.content.get(path=parent_path)
            if not obj:
                continue
            updated = 0
            conversation = IConversation(obj)

            for item in conversation_data["conversation"]["items"]:
                needs_update = (
                    isinstance(item["text"], dict)
                    and item["text"].get("data")
                    and item["text"].get("mime-type") == "text/html"
                )

                if needs_update:
                    comment_id = int(item["comment_id"])
                    comment = conversation._comments.get(comment_id)
                    if comment:
                        comment.text = RichTextValue(
                            item["text"]["data"], "text/html", "text/x-html-safe"
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
    

class ImportLocalRoles(import_other.ImportLocalRoles):

    index = ViewPageTemplateFile(
        "templates/import_localroles.pt",
        _prefix=os.path.dirname(import_other.__file__),
    )

    def import_localroles(self, data):
        results = 0
        total = len(data)
        for index, item in enumerate(data, start=1):
            obj_url = unquote(item["@id"])
            obj_path = urlparse(obj_url).path
            obj = api.content.get(path=obj_path)
            if not obj:
                if item["uuid"] == PORTAL_PLACEHOLDER:
                    obj = api.portal.get()
                else:
                    logger.info(
                        "Could not find object to set localroles on. UUID: {} ({})".format(
                            item["uuid"],
                            item["@id"],
                        )
                    )
                    continue
            if item.get("localroles"):
                localroles = item["localroles"]
                for userid in localroles:
                    obj.manage_setLocalRoles(userid=userid, roles=localroles[userid])
                logger.debug(
                    u"Set roles on {}: {}".format(obj.absolute_url(), localroles)
                )
            if item.get("block"):
                obj.__ac_local_roles_block__ = 1
                logger.debug(
                    u"Disable acquisition of local roles on {}".format(
                        obj.absolute_url()
                    )
                )
            if not index % 1000:
                logger.info(
                    u"Set local roles on {} ({}%) of {} items".format(
                        index, round(index / total * 100, 2), total
                    )
                )
            results += 1
        if results:
            logger.info("Reindexing Security")
            catalog = api.portal.get_tool("portal_catalog")
            pghandler = ZLogHandler(1000)
            catalog.reindexIndex("allowedRolesAndUsers", None, pghandler=pghandler)
        return results
