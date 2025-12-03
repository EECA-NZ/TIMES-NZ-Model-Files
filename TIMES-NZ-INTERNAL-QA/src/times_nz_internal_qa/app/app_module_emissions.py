"""
Data formatting, server and ui functions for emissions data

"""

from functools import lru_cache

import polars as pl
from shiny import reactive
from times_nz_internal_qa.app.helpers.data_processing import (
    aggregate_by_group,
    read_data_pl,
)
from times_nz_internal_qa.app.helpers.filters import (
    create_filter_dict,
)
from times_nz_internal_qa.app.helpers.server_functions import (
    register_server_functions_for_explorer,
)
from times_nz_internal_qa.app.helpers.ui_elements import make_explorer_page_ui
from times_nz_internal_qa.utilities.filepaths import FINAL_DATA

# CONSTANTS -----------------------------------------------------------

ID_PREFIX = "ems"
EMS_FILE_LOCATION = FINAL_DATA / "emissions.parquet"
# define base columns that we must always group by
base_cols = [
    "Scenario",
    "Period",
    "Variable",
    "Unit",
]

# define filter options with optional labels
# pylint: disable = duplicate-code
ems_filters_raw = [
    {"col": "SectorGroup", "label": "Sector Group"},
    {"col": "Sector"},
    {"col": "TechnologyGroup", "label": "Technology Group"},
    {"col": "Technology"},
    {"col": "EnduseGroup"},
    {"col": "EndUse"},
    {"col": "Region"},
    # {"col": "Process"},
    # {"col": "PlantName"},
]
# build filter dict
ems_filters = create_filter_dict("emissions", ems_filters_raw)
# base group options on defined filter options
ems_group_options = [d["col"] for d in ems_filters_raw]

ems_all_group_options = base_cols + ems_group_options


# EMISSIONS DATA ----------------------------------------------------------------

# Note: want to make an electricity-specific emissions chart too for emissions by plant


@lru_cache(maxsize=8)
def get_base_ems_df(scenarios, filepath=EMS_FILE_LOCATION):
    """
    Returns emsand data (pre-filtered)
    Based on scenario selections
    Caches results for quick switching
    """
    df = read_data_pl(filepath, scenarios)
    df = df.with_columns(pl.lit("Energy emissions").alias("Variable"))
    df = aggregate_by_group(df, ems_all_group_options)
    df = df.collect()
    return df


ems_parameters = {
    "page_id": ID_PREFIX,
    "chart_id": "ems",
    "sec_id": "ems-total",
    "filters": ems_filters,
    "section_title": "Energy emissions",
    "base_cols": base_cols,
    "group_options": ems_group_options,
}

# SERVER ----------------------------------------------------------------


def emissions_server(inputs, outputs, session, selected_scens):
    """
    server functions for emissions
    """

    @reactive.calc
    def scen_tuple():
        """Converting scenario list to tuple. needed for hashing"""
        return tuple(selected_scens["scenario_list"]())

    register_server_functions_for_explorer(
        ems_parameters, get_base_ems_df, scen_tuple, inputs, outputs, session
    )


# UI ---------------------------------------------------------------

sections = [ems_parameters]
emissions_ui = make_explorer_page_ui(sections, ID_PREFIX)
