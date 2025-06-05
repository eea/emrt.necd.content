from copy import deepcopy
from functools import partial
from pprint import pformat

from zope.interface import Interface

from zope.schema.vocabulary import SimpleVocabulary

from z3c.form import button
from z3c.form import form, field
from plone.z3cform.layout import wrap_form
from plone import schema
from plone.autoform.form import AutoExtensibleForm
from plone.supermodel import model
from plone.supermodel.directives import fieldset

from DateTime import DateTime
from Products.Five.browser import BrowserView

import plone.api as api

from emrt.necd.content.browser.carryover import catalog_with_children


class ReindexContext(BrowserView):
    def __call__(self):
        catalog = api.portal.get_tool("portal_catalog")
        catalog_with_children(catalog, self.context)
        return self.request.RESPONSE.redirect(self.context.absolute_url())


def cmp_datetime(cmp_date, entry):
    return cmp_date - entry["time"]


class IChangeHistoryForm(model.Schema):

    fieldset(
        "search",
        label="Search",
        fields=(
            "wf",
            "s_action",
            "s_actor",
            "s_author",
            "s_object",
            "s_review_state",
            "s_role",
            "s_state",
            "s_time",
        ),
    )
    wf = schema.Choice(
        title="Workflow id",
        values=[],
    )
    s_action = schema.Choice(title="Action", values=[], required=False)
    s_actor = schema.Choice(title="Actor", values=[], required=False)
    s_author = schema.Choice(title="Author", values=[], required=False)
    s_object = schema.Choice(title="Object", values=[], required=False)
    s_review_state = schema.Choice(
        title="Review state", values=[], required=False
    )
    s_role = schema.Choice(title="Role", values=[], required=False)
    s_state = schema.Choice(title="State", values=[], required=False)
    s_time = schema.Choice(title="Time", values=[], required=False)

    fieldset(
        "replace",
        label="Replace",
        fields=(
            "w_action",
            "w_actor",
            "w_author",
            "w_object",
            "w_review_state",
            "w_role",
            "w_state",
            "w_time",
        ),
    )
    w_action = schema.TextLine(title="Action", required=False)
    w_actor = schema.TextLine(title="Actor", required=False)
    w_author = schema.TextLine(title="Author", required=False)
    w_object = schema.TextLine(title="Object", required=False)
    w_review_state = schema.TextLine(title="Review state", required=False)
    w_role = schema.TextLine(title="Role", required=False)
    w_state = schema.TextLine(title="State", required=False)
    w_time = schema.TextLine(title="Time", required=False)


def vocabulary_from_history_items(items, name):
    return SimpleVocabulary.fromValues(
        sorted([x for x in {x.get(name, None) for x in items} if x])
    )


class ChangeHistoryForm(AutoExtensibleForm, form.Form):
    schema = IChangeHistoryForm
    ignoreContext = True

    def update(self):
        super(ChangeHistoryForm, self).update()
        wf_values = list(self.context.workflow_history.values())
        if wf_values:
            wf_values = wf_values[0]

        for group in self.groups:
            for fname in group.fields:
                if fname == "wf":
                    group.fields[fname].field.vocabulary = (
                        SimpleVocabulary.fromValues(
                            list(self.context.workflow_history.keys())
                        )
                    )

                elif fname.startswith("s_"):
                    group.fields[fname].field.vocabulary = (
                        vocabulary_from_history_items(wf_values, fname[2:])
                    )
        super(ChangeHistoryForm, self).update()

    def updateWidgets(self):
        super(ChangeHistoryForm, self).updateWidgets()

    def _parse_params(self, params):
        search_params = {
            k[2:]: v
            for k, v in params.items()
            if v is not None and k.startswith("s_")
        }
        search_time = search_params.pop("time", None)
        if search_time:
            search_params["time"] = DateTime(search_time)

        write_params = {
            k[2:]: v
            for k, v in params.items()
            if v is not None and k.startswith("w_")
        }
        if write_params.get("time"):
            write_params["time"] = DateTime(write_params["time"])

        return search_params, write_params

    def _find_entry(self, params, search_params):
        found = []

        entries = self.context.workflow_history[params["wf"]]

        for entry in entries:
            matched = [entry[k] == v for k, v in search_params.items()]
            if matched and all(matched):
                found.append(entry)

        return found[0] if found else None

    @button.buttonAndHandler("Delete matching")
    def handleDelete(self, action):
        params, errors = self.extractData()
        if errors:
            return False

        search_params, write_params = self._parse_params(params)
        target = self._find_entry(params, search_params)

        if target:
            wh = self.context.workflow_history
            wh[params["wf"]] = tuple(
                [x for x in wh[params["wf"]] if x != target]
            )

            self.context.workflow_history._p_changed = 1
            self.context._p_changed = 1
            self.context.reindexObject()

            api.portal.show_message(f"Removed entry {target}.")

        else:
            api.portal.show_message(
                f"Could not locate entry for: {search_params}."
            )

        self.request.response.redirect(self.context.absolute_url())

    @button.buttonAndHandler("Save")
    def handleSave(self, action):
        params, errors = self.extractData()
        if errors:
            return False

        search_params, write_params = self._parse_params(params)
        target = self._find_entry(params, search_params)

        if target:
            old_values = deepcopy(dict(target))

            for k, v in write_params.items():
                target[k] = v

            self.context.workflow_history._p_changed = 1
            self.context._p_changed = 1
            self.context.reindexObject()

            api.portal.show_message(
                f"Modified {pformat(old_values)} => {pformat(dict(target))}"
            )

        else:
            api.portal.show_message(
                f"Nothing modified for query: {pformat(params)}"
            )

        self.request.response.redirect(self.context.absolute_url())

    @button.buttonAndHandler("Cancel")
    def handleCancel(self, action):
        question = self.context.aq_parent
        self.request.response.redirect(self.context.absolute_url())


ChangeHistoryView = wrap_form(ChangeHistoryForm)
