"""
Data formatting, server and ui functions for electricity generation data

"""

from functools import lru_cache

import polars as pl
from shiny import reactive
from times_nz_internal_qa.app.helpers.data_processing import (
    aggregate_by_group,
    filter_df_for_variable,
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

# CONSTANTS  ------------------------------------------------------------------------------

PJ_TO_GWH = 277.778
# ID_PREFIX is used to ensure some ui and server elements link correctly
ID_PREFIX = "elec"
# data location
ELE_GEN_FILE_LOCATION = FINAL_DATA / "elec_generation.parquet"

# define base columns that we must always group by
# Might even make these standard across everything?
ele_base_cols = [
    "Scenario",
    "Variable",
    "Period",
    "Unit",
]
# parameters to optionally group data by
# Note: we can add Fuel for the fuel inputs
ele_core_group_options = [
    "TechnologyGroup",
    "Technology",
    "Region",
    "PlantName",
]

ele_fuel_group_options = ele_core_group_options + ["Fuel"]

# configure filter options
core_filters = [
    {"col": "TechnologyGroup", "label": "Technology Group"},
    {"col": "Technology"},
    {"col": "Region"},
    {"col": "PlantName", "label": "Plant"},
]

ele_gen_filters = create_filter_dict("ele_gen", core_filters)
ele_cap_filters = create_filter_dict("ele_cap", core_filters)
ele_use_filters = create_filter_dict("ele_use", core_filters + [{"col": "Fuel"}])

# all groups combined: used for processing main datasets
ele_all_group_options = ele_base_cols + ele_core_group_options + ["Fuel"]

# Define chart parameters
# here, we define the standard dictionaries for each chart.

ele_gen_parameters = {
    "page_id": ID_PREFIX,
    "chart_id": "ele_gen",
    "sec_id": "ele-gen",
    "filters": ele_gen_filters,
    "section_title": "Electricity generation",
    "base_cols": ele_base_cols,
    "group_options": ele_core_group_options,
}


ele_cap_parameters = {
    "page_id": ID_PREFIX,
    "chart_id": "ele_cap",
    "sec_id": "ele-cap",
    "filters": ele_cap_filters,
    "section_title": "Generation capacity",
    "base_cols": ele_base_cols,
    "group_options": ele_core_group_options,
}


ele_use_parameters = {
    "page_id": ID_PREFIX,
    "chart_id": "ele_use",
    "sec_id": "ele-use",
    "filters": ele_use_filters,
    "section_title": "Fuel used for generation",
    "base_cols": ele_base_cols,
    "group_options": ele_core_group_options,
}

# ELECTRICITY-SPECIFIC DATA HANDLING -----------------------------------------------

# CACHE MAIN TABLES

# We build separate functions for each table so they can all be cached separately.
# we define collection of the lazy frames at each of these points to hold cached data in memory
# this only updates when the scenario changes and caches 8 copies for common scenario configs


@lru_cache(maxsize=8)
def get_base_ele_gen_df(scenarios, filepath=ELE_GEN_FILE_LOCATION):
    """
    Returns ele gen data (pre-filtered)
    Based on scenario selections
    Caches results for quick switching
    """
    df = read_data_pl(filepath, scenarios)
    df = aggregate_by_group(df, ele_all_group_options)
    df = filter_df_for_variable(df, "Electricity generation", collect=True)

    # modify this for GWh

    df = df.with_columns(
        [(pl.col("Value") * PJ_TO_GWH).alias("Value"), pl.lit("GWh").alias("Unit")]
    )
    return df


@lru_cache(maxsize=8)
def get_base_ele_cap_df(scenarios, filepath=ELE_GEN_FILE_LOCATION):
    """
    Returns ele cap data (before any filtering)
    Based on scenario selections
    Caches results for quick switching
    """
    df = read_data_pl(filepath, scenarios)
    df = aggregate_by_group(df, ele_all_group_options)
    df = filter_df_for_variable(df, "Electricity generation capacity", collect=True)
    return df


@lru_cache(maxsize=8)
def get_base_ele_use_df(scenarios, filepath=ELE_GEN_FILE_LOCATION):
    """
    Returns ele use data (pre-filtered)
    Based on scenario selections
    Caches results for quick switching
    """
    df = read_data_pl(filepath, scenarios)
    df = aggregate_by_group(df, ele_all_group_options)
    df = filter_df_for_variable(df, "Electricity fuel use", collect=True)
    return df


# SERVER ------------------------------------------------------------------------


def elec_server(inputs, outputs, session, selected_scens):
    """
    server functions for electricity
    """

    @reactive.calc
    def scen_tuple():
        """Converting scenario list to tuple. needed for hashing"""
        return tuple(selected_scens["scenario_list"]())

    # register all functions

    register_server_functions_for_explorer(
        ele_gen_parameters, get_base_ele_gen_df, scen_tuple, inputs, outputs, session
    )

    register_server_functions_for_explorer(
        ele_cap_parameters, get_base_ele_cap_df, scen_tuple, inputs, outputs, session
    )

    register_server_functions_for_explorer(
        ele_use_parameters, get_base_ele_use_df, scen_tuple, inputs, outputs, session
    )


# UI ------------------------------------------------

# just gather parameters in a list and send to explorer page function

sections = [
    ele_gen_parameters,
    ele_use_parameters,
    ele_cap_parameters,
]

elec_ui = make_explorer_page_ui(sections, ID_PREFIX)
