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
# pylint:disable = duplicate-code
# all modules get a unique id code to generate other IDs with
ID_PREFIX = "dem"

PJ_TO_GWH = 277.778
DEM_FILE_LOCATION = FINAL_DATA / "energy_demand.parquet"
ELC_DEM_CURVE_FILE = FINAL_DATA / "electricity_demand_by_timeslice.parquet"
TRANSPORT_ENERGY_DEMAND_FILE = FINAL_DATA / "transport_energy_demand.parquet"
TRANSPORT_CAPACITY_FILE = FINAL_DATA / "transport_capacity.parquet"
TECHNOLOGY_CAPACITY_FILE = FINAL_DATA / "technology_capacity.parquet"

# SET FILTER/GROUP OPTIONS

dem_filters = [
    {"col": "SectorGroup"},
    {"col": "Sector"},
    {"col": "Fuel"},
    {"col": "TechnologyGroup"},
    {"col": "Technology"},
    {"col": "EnduseGroup"},
    {"col": "EndUse"},
    {"col": "Region"},
]

technology_capacity_filters = [
    {"col": "SectorGroup"},
    {"col": "Sector"},
    {"col": "TechnologyGroup"},
    {"col": "Technology"},
    {"col": "EnduseGroup"},
    {"col": "EndUse"},
    {"col": "Region"},
]


elc_dem_filters = [
    {"col": "SectorGroup"},
    {"col": "Sector"},
    {"col": "TechnologyGroup"},
    {"col": "Technology"},
    {"col": "EnduseGroup"},
    {"col": "EndUse"},
    {"col": "Region"},
]

elc_dem_curve_filters = [
    {"col": "Period", "multiple": False, "label": "Year"},
    {"col": "SectorGroup"},
    {"col": "Sector"},
    {"col": "TechnologyGroup"},
    {"col": "Technology"},
    {"col": "EnduseGroup"},
    {"col": "EndUse"},
    {"col": "Region"},
]
# we add fuel to main

dem_filters = create_filter_dict("energy_dem", dem_filters)
technology_capacity_filters = create_filter_dict(
    "technology_capacity", technology_capacity_filters
)
elc_dem_filters = create_filter_dict("elc_dem", elc_dem_filters)
elc_dem_curve_filters = create_filter_dict("elc_dem_curve", elc_dem_curve_filters)

dem_group_options = [d["col"] for d in dem_filters]
technology_capacity_group_options = [d["col"] for d in technology_capacity_filters]
elc_dem_group_options = [d["col"] for d in elc_dem_filters]

# Core variables we always group by

base_cols = [
    "Scenario",
    "Variable",
    "Period",
    "Unit",
]

dem_all_group_options = base_cols + dem_group_options
technology_capacity_all_group_options = base_cols + technology_capacity_group_options
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

technology_capacity_parameters = {
    "page_id": ID_PREFIX,
    "chart_id": "technology_capacity",
    "sec_id": "technology-capacity",
    "filters": technology_capacity_filters,
    "section_title": "Technology Capacity",
    "base_cols": base_cols,
    "group_options": technology_capacity_group_options,
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
    "chart_type": "timeslice",
}


elc_dem_curve_all_groups = (
    elc_dem_curve_parameters["base_cols"] + elc_dem_group_options
)

# TRANSPORT-SPECIFIC CONSTANTS (Energy Demand & Capacity) -----

# define base columns that we must always group by
transport_base_cols = [
    "Scenario",
    "Variable",
    "Period",
    "Unit",
]

# configure filter options
transport_filters = [
    {"col": "Sector", "label": "Transport Sector"},
    {"col": "Utilisation"},
    {"col": "TechnologyGroup"},
    {"col": "Technology"},
    {"col": "EnduseGroup"},
    {"col": "EndUse"},
    {"col": "Region"},
]

transport_energy_demand_filters = create_filter_dict("transport_ed", transport_filters)
transport_capacity_filters = create_filter_dict("transport_capacity", transport_filters)

# Extract group options from filters
transport_group_options = [d["col"] for d in transport_filters]
transport_all_group_options = transport_base_cols + transport_group_options

transport_energy_demand_parameters = {
    "page_id": ID_PREFIX,
    "chart_id": "transport_ed",
    "sec_id": "transport-ed",
    "filters": transport_energy_demand_filters,
    "section_title": "Transport Energy Demand",
    "base_cols": transport_base_cols,
    "group_options": transport_group_options,
}

transport_capacity_parameters = {
    "page_id": ID_PREFIX,
    "chart_id": "transport_capacity",
    "sec_id": "transport-capacity",
    "filters": transport_capacity_filters,
    "section_title": "Transport Capacity",
    "base_cols": transport_base_cols,
    "group_options": transport_group_options,
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
def get_base_technology_capacity_df(scenarios, filepath=TECHNOLOGY_CAPACITY_FILE):
    """
    Returns non-transport technology capacity data (pre-filtered)
    Based on scenario selections
    Caches results for quick switching
    """
    df = read_data_pl(filepath, scenarios)
    df = aggregate_by_group(df, technology_capacity_all_group_options)
    df = filter_df_for_variable(df, "Technology Capacity", collect=True)
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


@lru_cache(maxsize=8)
def get_base_elc_dem_curve_df(scenarios, filepath=ELC_DEM_CURVE_FILE):
    """
    Returns electricity demand data (pre-filtered)
    Adjusts to GWh
    Based on scenario selections
    Caches results for quick switching
    """
    df = read_data_pl(filepath, scenarios)
    df = aggregate_by_group(df, elc_dem_curve_all_groups)

    # electricity demand only

    return df.collect()


@lru_cache(maxsize=8)
def get_base_transport_energy_demand_df(
    scenarios, filepath=TRANSPORT_ENERGY_DEMAND_FILE
):
    """
    Returns transport energy demand data with utilization breakdown
    Based on scenario selections
    Caches results for quick switching
    """
    df = read_data_pl(filepath, scenarios)
    df = aggregate_by_group(df, transport_all_group_options)
    df = filter_df_for_variable(df, "Transport Energy Demand", collect=True)
    return df


@lru_cache(maxsize=8)
def get_base_transport_capacity_df(scenarios, filepath=TRANSPORT_CAPACITY_FILE):
    """
    Returns transport capacity data with utilization breakdown
    Based on scenario selections
    Caches results for quick switching
    """
    df = read_data_pl(filepath, scenarios)
    df = aggregate_by_group(df, transport_all_group_options)
    df = filter_df_for_variable(df, "Transport Capacity", collect=True)
    return df


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
        dem_parameters,
        get_base_dem_df,
        scen_tuple,
        selected_scens["is_comparison"],
        inputs,
        outputs,
        session,
    )

    register_server_functions_for_explorer(
        technology_capacity_parameters,
        get_base_technology_capacity_df,
        scen_tuple,
        selected_scens["is_comparison"],
        inputs,
        outputs,
        session,
    )

    register_server_functions_for_explorer(
        elc_dem_parameters,
        get_base_elc_dem_df,
        scen_tuple,
        selected_scens["is_comparison"],
        inputs,
        outputs,
        session,
    )

    register_server_functions_for_explorer(
        elc_dem_curve_parameters,
        get_base_elc_dem_curve_df,
        scen_tuple,
        selected_scens["is_comparison"],
        inputs,
        outputs,
        session,
    )

    register_server_functions_for_explorer(
        transport_energy_demand_parameters,
        get_base_transport_energy_demand_df,
        scen_tuple,
        selected_scens["is_comparison"],
        inputs,
        outputs,
        session,
    )

    register_server_functions_for_explorer(
        transport_capacity_parameters,
        get_base_transport_capacity_df,
        scen_tuple,
        selected_scens["is_comparison"],
        inputs,
        outputs,
        session,
    )


# UI --------------------------------------------


sections = [
    dem_parameters,
    technology_capacity_parameters,
    elc_dem_parameters,
    elc_dem_curve_parameters,
    transport_energy_demand_parameters,
    transport_capacity_parameters,
]


demand_ui = make_explorer_page_ui(
    sections,
    ID_PREFIX,
    page_info_button_id="info_dem",
)
