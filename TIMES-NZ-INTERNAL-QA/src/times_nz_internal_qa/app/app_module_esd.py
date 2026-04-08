"""
App explorer page for energy service demand

Kind of a funky one since we will be using sectors that cannot be stacked

So the sector filter requires no multi options

Will need to build that into main
"""

from functools import lru_cache

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

# CONSTANTS -----------------------------------------------------------
# pylint:disable = duplicate-code

ID_PREFIX = "esd"
ESD_FILE_LOCATION = FINAL_DATA / "energy_service_demand.parquet"
ESD_CURVE_FILE_LOCATION = FINAL_DATA / "esd_by_timeslice.parquet"
TRANSPORT_ESD_FILE = FINAL_DATA / "transport_energy_service_demand.parquet"


# define base columns that we must always group by
# Might even make these standard across everything?
base_cols = [
    "Scenario",
    "Variable",
    "Period",
    "Unit",
]


esd_curve_base_cols = [
    "Scenario",
    "Variable",
    "TimeSlice",
    "Period",
    "Unit",
]


# Filter options
core_filters = [
    {"col": "SectorGroup", "label": "Sector Group"},
    {"col": "Sector"},
    {"col": "EnduseGroup", "label": "End Use Group"},
    {"col": "EndUse", "label": "End Use"},
    {"col": "TechnologyGroup", "label": "Technology Group"},
    {"col": "Technology"},
    # {"col": "Process"},
    {"col": "Region"},
]


curve_filters = [
    # need to have Sector be at the top and not allow multiselect
    # have added optional multiple parameter (defaults to true)
    {"col": "Period", "multiple": False, "label": "Year"},
    {"col": "SectorGroup", "label": "Sector Group"},
    {"col": "Sector"},
    {"col": "EnduseGroup", "label": "End Use Group"},
    {"col": "EndUse", "label": "End Use"},
    {"col": "TechnologyGroup", "label": "Technology Group"},
    {"col": "Technology"},
    # {"col": "Process"},
    {"col": "Region"},
]

esd_filters = create_filter_dict("esd", core_filters)
esd_curve_filters = create_filter_dict("esd_curve", curve_filters)
# Group options (combine core and options)
esd_group_options = [d["col"] for d in core_filters]
esd_all_group_options = base_cols + esd_group_options

# PARAMETER DICTIONARIES

esd_parameters = {
    "page_id": ID_PREFIX,
    "chart_id": "esd",
    "sec_id": "esd-total",
    "filters": esd_filters,
    "section_title": "Energy service demand PJ",
    "base_cols": base_cols,
    "group_options": esd_group_options,
}

esd_curve_parameters = {
    "page_id": ID_PREFIX,
    "chart_id": "esd_curve",
    "sec_id": "esd-curve",
    "filters": esd_curve_filters,
    "section_title": "Energy service demand by timeslice",
    "base_cols": esd_curve_base_cols,
    "group_options": esd_group_options,
    "chart_type": "timeslice",
}


esd_curve_all_group_options = (
    esd_curve_parameters["base_cols"] + esd_curve_parameters["group_options"]
)


# TRANSPORT-SPECIFIC CONSTANTS (ESD) -----

# define base columns that we must always group by
transport_esd_base_cols = [
    "Scenario",
    "Variable",
    "Period",
    "Unit",
]

# configure filter options
transport_esd_filters_list = [
    {"col": "EnduseGroup", "label": "End Use Group"},
    {"col": "EndUse", "label": "End Use"},
    {"col": "TechnologyGroup", "label": "Technology Group"},
    {"col": "Technology"},
    {"col": "Utilisation"},
    {"col": "Region"},
]

transport_esd_filters = create_filter_dict("transport_esd", transport_esd_filters_list)

# Extract group options from filters
transport_esd_group_options = [d["col"] for d in transport_esd_filters_list]
transport_esd_all_group_options = transport_esd_base_cols + transport_esd_group_options

transport_esd_parameters = {
    "page_id": ID_PREFIX,
    "chart_id": "transport_esd",
    "sec_id": "transport-esd",
    "filters": transport_esd_filters,
    "section_title": "Energy service demand VKT",
    "base_cols": transport_esd_base_cols,
    "group_options": transport_esd_group_options,
}


# Energy Service Demand Data ----------------------------------------------------------------


@lru_cache(maxsize=8)
def get_base_esd_df(scenarios, filepath=ESD_FILE_LOCATION):
    """
    Returns ESD data pre-filtering
    Based on scenario selections
    Caches results for quick switching
    """
    df = read_data_pl(filepath, scenarios)
    df = aggregate_by_group(df, esd_all_group_options)
    df = df.collect()

    return df


@lru_cache(maxsize=8)
def get_base_esd_curve_df(scenarios, filepath=ESD_CURVE_FILE_LOCATION):
    """
    Returns ESD data pre-filtering
    Based on scenario selections
    Caches results for quick switching
    """
    df = read_data_pl(filepath, scenarios)
    df = aggregate_by_group(df, esd_curve_all_group_options)
    df = df.collect()

    return df


@lru_cache(maxsize=8)
def get_base_transport_esd_df(scenarios, filepath=TRANSPORT_ESD_FILE):
    """
    Returns transport energy service demand data with utilization breakdown
    Based on scenario selections
    Caches results for quick switching
    """
    df = read_data_pl(filepath, scenarios)
    df = aggregate_by_group(df, transport_esd_all_group_options)
    df = filter_df_for_variable(df, "Transport Energy Service Demand", collect=True)
    return df


# SERVER ----------------------------------------------------------------


def energy_service_demand_server(inputs, outputs, session, selected_scens):
    """
    Register energy service demand server functions
    """

    # GET DATA BASED ON SCENARIO SELECTION
    @reactive.calc
    def scen_tuple():
        """Converting scenario list to tuple. needed for hashing"""
        return tuple(selected_scens["scenario_list"]())

    register_server_functions_for_explorer(
        esd_parameters,
        get_base_esd_df,
        scen_tuple,
        selected_scens["is_comparison"],
        inputs,
        outputs,
        session,
    )

    # register_server_functions_for_explorer(
    #     esd_curve_parameters,
    #     get_base_esd_curve_df,
    #     scen_tuple,
    #     selected_scens["is_comparison"],
    #     inputs,
    #     outputs,
    #     session,
    # )

    register_server_functions_for_explorer(
        transport_esd_parameters,
        get_base_transport_esd_df,
        scen_tuple,
        selected_scens["is_comparison"],
        inputs,
        outputs,
        session,
    )


# UI ---------------------------------------------------------------

sections = [
    esd_parameters,
    # esd_curve_parameters,
    transport_esd_parameters,
]
esd_ui = make_explorer_page_ui(
    sections,
    ID_PREFIX,
    page_info_button_id="info_esd",
)
