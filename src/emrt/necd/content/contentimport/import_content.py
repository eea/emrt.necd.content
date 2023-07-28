from zope.schema import getFieldNames

from collective.exportimport.import_content import ImportContent

from emrt.necd.content.observation import IObservation

SIMPLE_SETTER_FIELDS = {
    # "ALL": ["some_shared_field"],
    "Observation": getFieldNames(IObservation),
}


class CustomImportContent(ImportContent):
    def global_dict_hook(self, item):
        simple = {}
        # for fieldname in SIMPLE_SETTER_FIELDS.get("ALL", []):
        #     if fieldname in item:
        #         value = item.pop(fieldname)
        #         if value:
        #             simple[fieldname] = value
        item_type = item["@type"]

        # fix int year
        if (
            item_type == "Observation"
            and "year" in item
            and isinstance(item["year"], int)
        ):
            item["year"] = str(item["year"])

        for fieldname in SIMPLE_SETTER_FIELDS.get(item_type, []):
            if fieldname in item:
                value = item.pop(fieldname)
                if value:
                    simple[fieldname] = value
        if simple:
            item["exportimport.simplesetter"] = simple

        return item

    def global_obj_hook_before_deserializing(self, obj, item):
        """Hook to modify the created obj before deserializing the data."""
        # import simplesetter data before the rest
        for fieldname, value in item.get(
            "exportimport.simplesetter", {}
        ).items():
            setattr(obj, fieldname, value)

        return obj, item
