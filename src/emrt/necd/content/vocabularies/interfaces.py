"""plone.app.registry settings."""

import os

from zope.interface import Interface

from plone import schema

from emrt.necd.content import _

CSV_PATH = os.path.join(os.path.dirname(__file__), "data")


def read_profile_vocabulary(filename: str) -> str:
    """Read the contents of CSV_PATH/filename."""
    result = ""
    with open(os.path.join(CSV_PATH, filename), "r") as infile:
        result = infile.read().strip()
    return result


class INECDVocabularies(Interface):
    """Definition for Plone Registry."""
    projection_pollutants = schema.Dict(
        title=_("Projection pollutants vocabulary"),
        description=_(
            "Registers the values for pollutants in the context of "
            "a Projection ReviewFolder"
        ),
        key_type=schema.TextLine(title=_("Pollutant key")),
        value_type=schema.TextLine(
            title=_("Pollutant value"),
        ),
    )

    projection_parameter = schema.List(
        title=_("Projection parameter vocabulary"),
        description=_(
            "Registers the values for parameter in the context of "
            "a Projection ReviewFolder"
        ),
        value_type=schema.Dict(
            key_type=schema.TextLine(title=_("Key")),
            value_type=schema.TextLine(
                title=_("Value"),
            ),
        ),
    )

    activity_data = schema.Dict(
        title=_("Activity data"),
        description=_("Registers the activity data"),
        key_type=schema.TextLine(title=_("Activity data type")),
        value_type=schema.List(
            value_type=schema.TextLine(
                title=_("Activity data"),
            ),
        ),
    )

    eea_member_states = schema.Text(
        title=_("EEA Member States"),
        default=read_profile_vocabulary("eea_member_states.csv"),
    )

    ghg_source_category = schema.Text(
        title=_("NFR category group"),
        default=read_profile_vocabulary("ghg_source_category.csv"),
    )

    ghg_source_sectors = schema.Text(
        title=_("NFR Sector"),
        default=read_profile_vocabulary("ghg_source_sectors.csv"),
    )

    fuel = schema.Text(
        title=_("Fuel"),
        default=read_profile_vocabulary("fuel.csv"),
    )

    pollutants = schema.Text(
        title=_("Pollutants"),
        default=read_profile_vocabulary("pollutants.csv"),
    )

    scenario_type = schema.Text(
        title=_("Scenario Type"),
        default=read_profile_vocabulary("scenario_type.csv"),
    )

    highlight = schema.Text(
        title=_("Highlight"),
        default=read_profile_vocabulary("highlight.csv"),
    )

    highlight_2024_onwards = schema.Text(
        title=_("Highlight 2024 onwards"),
        default=read_profile_vocabulary("highlight_2024_onwards.csv"),
    )

    highlight_2025_onwards = schema.Text(
        title=_("Highlight 2025 onwards"),
        default=read_profile_vocabulary("highlight_2025_onwards.csv"),
    )

    highlight_projection = schema.Text(
        title=_("Highlight Projection"),
        default=read_profile_vocabulary("highlight_projection.csv"),
    )

    highlight_projection_2025_onwards = schema.Text(
        title=_("Highlight Projection 2025 onwards"),
        default=read_profile_vocabulary("highlight_projection_2025_onwards.csv"),
    )

    highlight_vocabulary_types = schema.Text(
        title=_("Highlight Vocabulary Types"),
        default=read_profile_vocabulary("highlight_vocabulary_types.csv"),
    )

    parameter = schema.Text(
        title=_("Parameter"),
        default=read_profile_vocabulary("parameter.csv"),
    )

    conclusion_reasons = schema.Text(
        title=_("Conclusion Reasons"),
        default=read_profile_vocabulary("conclusion_reasons.csv"),
    )
