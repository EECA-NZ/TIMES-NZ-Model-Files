"""
Energy demand processing, ui, and server functions
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

# CONSTANTS --------------------------------------------------

# all modules get a unique id code to generate other IDs with
ID_PREFIX = "dem"

PJ_TO_GWH = 277.778
DEM_FILE_LOCATION = FINAL_DATA / "energy_demand.parquet"

# SET FILTER/GROUP OPTIONS

dem_filters_raw = [
    {"col": "SectorGroup", "label": "Sector Group"},
    {"col": "Sector"},
    {"col": "TechnologyGroup", "label": "Technology Group"},
    {"col": "Technology"},
    {"col": "EnduseGroup"},
    {"col": "EndUse"},
    {"col": "Region"},
    {"col": "Process"},
]


elc_dem_curve_filters = [
    {"col": "Period", "multiple": False, "label": "Year"},
    {"col": "SectorGroup", "label": "Sector Group"},
    {"col": "Sector"},
    {"col": "TechnologyGroup", "label": "Technology Group"},
    {"col": "Technology"},
    {"col": "EnduseGroup"},
    {"col": "EndUse"},
    {"col": "Region"},
    {"col": "Process"},
]
# we add fuel to main
dem_filters = dem_filters_raw + [{"col": "Fuel"}]
dem_filters = create_filter_dict("energy_dem", dem_filters)
elc_dem_filters = create_filter_dict("elc_dem", dem_filters_raw)
elc_dem_curve_filters = create_filter_dict("elc_dem_curve", dem_filters_raw)

dem_group_options = [d["col"] for d in dem_filters]
elc_dem_group_options = [d["col"] for d in elc_dem_filters]

# Core variables we always group by

base_cols = [
    "Scenario",
    "Variable",
    "Period",
    "Unit",
]

dem_all_group_options = base_cols + dem_group_options
elc_dem_all_group_options = base_cols + elc_dem_group_options


# SET PARAMETERS

dem_parameters = {
    "page_id": ID_PREFIX,
    "chart_id": "energy_dem",
    "sec_id": "energy-dem",
    "filters": dem_filters,
    "section_title": "Total energy demand",
    "base_cols": base_cols,
    "group_options": dem_group_options,
}

elc_dem_parameters = {
    "page_id": ID_PREFIX,
    "chart_id": "elc_dem",
    "sec_id": "elc-dem",
    "filters": elc_dem_filters,
    "section_title": "Electricity demand",
    "base_cols": base_cols,
    "group_options": elc_dem_group_options,
}


elc_dem_curve_parameters = {
    "page_id": ID_PREFIX,
    "chart_id": "elc_dem_curve",
    "sec_id": "elc-dem-curve",
    "filters": elc_dem_curve_filters,
    "section_title": "Electricity demand by timeslice",
    "base_cols": base_cols + ["TimeSlice"],
    "group_options": elc_dem_group_options,
}


# GET DATA ------------------------------------------


@lru_cache(maxsize=8)
def get_base_dem_df(scenarios, filepath=DEM_FILE_LOCATION):
    """
    Returns demand data (pre-filtered)
    Based on scenario selections
    Caches results for quick switching
    """
    df = read_data_pl(filepath, scenarios)
    df = aggregate_by_group(df, dem_all_group_options)
    df = filter_df_for_variable(df, "Energy demand", collect=True)
    return df


@lru_cache(maxsize=8)
def get_base_elc_dem_df(scenarios, filepath=DEM_FILE_LOCATION):
    """
    Returns electricity demand data (pre-filtered)
    Adjusts to GWh
    Based on scenario selections
    Caches results for quick switching
    """
    df = read_data_pl(filepath, scenarios)
    df = aggregate_by_group(df, dem_all_group_options)

    # electricity demand only
    df = df.filter(pl.col("Fuel") == "Electricity")

    # don't collect yet - we want to do further modifications
    df = filter_df_for_variable(df, "Energy demand", collect=False)

    # convert gwh and change variable
    df = df.with_columns(
        [
            (pl.col("Value") * PJ_TO_GWH).alias("Value"),
            pl.lit("GWh").alias("Unit"),
            pl.lit("Electricity demand").alias("Variable"),
        ]
    )

    return df.collect()


# SERVER ------------------------------------------


# pylint:disable = too-many-locals, unused-argument, too-many-statements
def demand_server(inputs, outputs, session, selected_scens):
    """
    Server functions for energy demand module
    """

    @reactive.calc
    def scen_tuple():
        """Converting scenario list to tuple. needed for hashing"""
        return tuple(selected_scens["scenario_list"]())

    register_server_functions_for_explorer(
        dem_parameters, get_base_dem_df, scen_tuple, inputs, outputs, session
    )

    register_server_functions_for_explorer(
        elc_dem_parameters, get_base_elc_dem_df, scen_tuple, inputs, outputs, session
    )

    register_server_functions_for_explorer(
        elc_dem_curve_parameters,
        get_base_elc_dem_df,
        scen_tuple,
        inputs,
        outputs,
        session,
    )


# UI --------------------------------------------


sections = [
    elc_dem_curve_parameters,
    dem_parameters,
    elc_dem_parameters,
]


demand_ui = make_explorer_page_ui(sections, ID_PREFIX)
