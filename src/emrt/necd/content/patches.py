"""Patches."""

from lxml import etree
import json

import hashlib
from logging import getLogger
from typing import List

from Products.CMFDiffTool import dexteritydiff
from plone.app.z3cform.widgets.richtext import RichTextWidgetBase

from plone.memoize.ram import cache

EXCLUDED_FIELDS: List[str] = list(dexteritydiff.EXCLUDED_FIELDS)
EXCLUDED_FIELDS.append("ghg_estimations")
dexteritydiff.EXCLUDED_FIELDS = tuple(EXCLUDED_FIELDS)

log = getLogger(__name__)
log.info("Patching difftool excluded fields to add ghg_estimations")


def _sha_cachekey(sig):
    return hashlib.sha256(str(sig).encode()).hexdigest()


@property
def Group_existing_member_ids(self):
    """Patched Group.existing_member_ids."""
    return self.translate_ids(
        self.context.attrs.get(self._member_attribute, list())
    )


def LDAPUserPropertySheet__init__(self, principal, plugin):
    """Patched LDAPUserPropertySheet.__init__.

    Join fullname if it's a list.
    """
    self._old___init__(principal, plugin)
    fullname = self._properties.get("fullname", "")
    if isinstance(fullname, (list, tuple)):
        self._properties["fullname"] = " ".join(fullname)


def _items_from_dict(d):
    if isinstance(d, dict):
        return tuple([(k, _items_from_dict(v)) for k, v in d.items()])
    return d


def _cachekey(meth, self, *args, **kwargs):
    kw = _items_from_dict(kwargs)
    sig = (meth.__name__, self.__name__, args, kw)
    return _sha_cachekey(sig)


@cache(_cachekey)
def cache_wrapper(meth, *args, **kwargs):
    """Wrapper."""
    return meth(*args, **kwargs)


def LDAPPrincipals_search(self, *args, **kwargs):
    """Patch LDAPPrincipals.search."""
    result = cache_wrapper(self._old_search, *args, **kwargs)
    return result


def RichTextWidget_render_input_mode(self):
    # MODE "INPUT"
    rendered = ""
    allowed_mime_types = self.allowedMimeTypes()
    if not allowed_mime_types or len(allowed_mime_types) <= 1:
        # Display textarea with default widget
        rendered = super().render()
    else:
        # Let pat-textarea-mimetype-selector choose the widget

        # create a copy of RichTextWidget
        textarea_widget = RichTextWidgetBase(self.request)
        textarea_widget.field = self.field
        textarea_widget.name = self.name
        textarea_widget.value = self.value
        textarea_widget.form = self.form

        mt_pattern_name = "{}{}".format(
            self._klass_prefix,
            "textareamimetypeselector",
        )

        # Initialize mimetype selector pattern
        # TODO: default_mime_type returns 'text/html', regardless of
        # settings. fix in plone.app.textfield
        value_mime_type = (
            self.value.mimeType if self.value else self.field.default_mime_type
        )
        mt_select = etree.Element("select")
        mt_select.attrib["id"] = f"{self.id}_text_format"
        mt_select.attrib["name"] = f"{self.name}.mimeType"
        mt_select.attrib["class"] = f"form-select {mt_pattern_name}"
        mt_select.attrib[f"data-{mt_pattern_name}"] = json.dumps(
            {
                "textareaName": self.name,
                "widgets": {
                    "text/html": {  # TODO: currently, we only support
                        # richtext widget config for
                        # 'text/html', no other mimetypes.
                        "pattern": self.pattern,
                        "patternOptions": self.get_pattern_options(),
                    },
                },
            },
        )

        # Create a list of allowed mime types
        for mt in allowed_mime_types:
            opt = etree.Element("option")
            opt.attrib["value"] = mt
            if value_mime_type == mt:
                opt.attrib["selected"] = "selected"
            opt.text = mt
            mt_select.append(opt)

        # Render the combined widget
        textarea_widget.update()
        rendered = "{}\n{}".format(
            textarea_widget.render(),
            etree.tostring(mt_select, encoding="unicode"),
        )
    return rendered
