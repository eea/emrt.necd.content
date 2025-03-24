from urllib.parse import unquote
from urllib.parse import urlparse

from collective.exportimport.import_content import ImportContent

import plone.api as api

SIMPLE_SETTER_FIELDS = {
    # "ALL": ["some_shared_field"],
    "Conclusions": [
      "ghg_estimations",
    ],
    "Observation": [
        "country",
        "nfr_code",
        "year",
        "nfr_code_inventory",
        "pollutants",
        "scenario",
        "fuel",
        "activity_data_type",
        "activity_data",
        "parameter",
        "highlight",
    ],
}


class CustomImportContent(ImportContent):

    def global_dict_hook(self, item):
        simple = {}
        # for fieldname in SIMPLE_SETTER_FIELDS.get("ALL", []):
        #     if fieldname in item:
        #         value = item.pop(fieldname)
        #         if value:
        #             simple[fieldname] = value
        if not item["title"]:
            item["title"] = item["id"]

        for fieldname in SIMPLE_SETTER_FIELDS.get(item["@type"], []):
            if fieldname in item:
                value = item.pop(fieldname)
                if value:
                    simple[fieldname] = value
        if simple:
            item["exportimport.simplesetter"] = simple

        return item

    def get_parent_as_container(self, item):
        """Get parent by path, not by UID, there were issues with duplicate UIDs in import data."""
        parent_url = unquote(item["parent"]["@id"])
        parent_path = urlparse(parent_url).path
        return api.content.get(path=parent_path)

    def global_obj_hook_before_deserializing(self, obj, item):
        to_set = item.get("exportimport.simplesetter", {}).items()

        for fieldname, value in to_set:
            setattr(obj, fieldname, value)

        return obj, item
