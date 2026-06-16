"""
App processing for developer-facing QA views
"""

from functools import lru_cache
from pathlib import Path

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

## Quite messy input data processing
# pylint:disable = duplicate-code

# CONSTANTS ---------------------------------------

ID_PREFIX = "dev"


CLEAN_RESULTS = Path(FINAL_DATA).parent / "clean_results"
DUMMY_ENERGY_FILEPATH = CLEAN_RESULTS / "dummy_energy.parquet"
DUMMY_DEMAND_FILEPATH = CLEAN_RESULTS / "dummy_demand.parquet"
TECHNOLOGY_CAPACITY_FILE = FINAL_DATA / "technology_capacity.parquet"

dummy_energy_group_options = ["Commodity", "Region", "Fuel"]
dummy_demand_group_options = [
    "SectorGroup",
    "Sector",
    "EndUse",
    "Commodity",
    "Region",
]
technology_capacity_group_options = [
    "SectorGroup",
    "Sector",
    "TechnologyGroup",
    "Technology",
    "EnduseGroup",
    "EndUse",
    "Region",
    "Process",
]


# define filter options. see create_filter_dict for details
# ONE PER SECTION
dummy_demand_filters = create_filter_dict(
    "dummy_demand",  # chart id for all of these
    # list of dicts
    [
        {"col": "SectorGroup"},
        {"col": "Sector"},
        {"col": "EndUse"},
        {"col": "Commodity"},
        {"col": "Region"},
    ],
)

dummy_energy_filters = create_filter_dict(
    "dummy_energy",
    [
        {"col": "Fuel"},
        {"col": "Region"},
        {"col": "Commodity"},
    ],
)

technology_capacity_filters = create_filter_dict(
    "technology_capacity",
    [
        {"col": "SectorGroup"},
        {"col": "Sector"},
        {"col": "TechnologyGroup"},
        {"col": "Technology"},
        {"col": "EnduseGroup"},
        {"col": "EndUse"},
        {"col": "Region"},
    ],
)


# Specific data processing

base_cols = ["Scenario", "Period", "Variable", "Unit"]
technology_capacity_all_group_options = base_cols + technology_capacity_group_options


# GET MAIN DATA
@lru_cache(maxsize=8)
def get_dev_energy_df(scenarios, filepath=DUMMY_ENERGY_FILEPATH):
    """
    standard
    """
    all_group_options = base_cols + dummy_energy_group_options
    df = read_data_pl(filepath, scenarios)
    # add a unit (we didn't bother in preprocessing)
    df = df.with_columns(pl.lit("PJ").alias("Unit"))
    df = aggregate_by_group(df, all_group_options)
    # collect. No variable filters.
    return df.collect()


@lru_cache(maxsize=8)
def get_dev_demand_df(scenarios, filepath=DUMMY_DEMAND_FILEPATH):
    """
    standard
    """
    all_group_options = base_cols + dummy_demand_group_options
    df = read_data_pl(filepath, scenarios)
    # add a unit (we didn't bother in preprocessing)
    df = df.with_columns(pl.lit("PJ").alias("Unit"))
    df = aggregate_by_group(df, all_group_options)
    # collect. No variable filters.
    return df.collect()


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


developer_energy_parameters = {
    "page_id": ID_PREFIX,
    "chart_id": "dev_nrg",
    "sec_id": "dev-nrg",
    "filters": dummy_energy_filters,
    "section_title": "Infeasible energy",
    "base_cols": base_cols,
    "group_options": dummy_energy_group_options,
}

developer_demand_parameters = {
    "page_id": ID_PREFIX,
    "chart_id": "dev_dem",
    "sec_id": "dev-dem",
    "filters": dummy_demand_filters,
    "section_title": "Infeasible service demand",
    "base_cols": base_cols,
    "group_options": dummy_demand_group_options,
}

technology_capacity_parameters = {
    "page_id": ID_PREFIX,
    "chart_id": "technology_capacity",
    "sec_id": "technology-capacity",
    "filters": technology_capacity_filters,
    "section_title": "Technology capacity",
    "base_cols": base_cols,
    "group_options": technology_capacity_group_options,
}

# SERVER ------------------------------------------------------------------


def developers_server(inputs, outputs, session, selected_scens):
    """
    Server functions for dummy process module
    """

    # GET DATA BASED ON SCENARIO SELECTION
    @reactive.calc
    def scen_tuple():
        """Converting scenario list to tuple. needed for hashing"""
        return tuple(selected_scens["scenario_list"]())

    register_server_functions_for_explorer(
        developer_demand_parameters,
        get_dev_demand_df,
        scen_tuple,
        selected_scens["is_comparison"],
        inputs,
        outputs,
        session,
    )

    register_server_functions_for_explorer(
        developer_energy_parameters,
        get_dev_energy_df,
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


# UI --------------------------------------------------


sections = [
    developer_demand_parameters,
    developer_energy_parameters,
    technology_capacity_parameters,
]


developers_ui = make_explorer_page_ui(
    sections,
    ID_PREFIX,
    page_info_button_id="info_dev",
)
