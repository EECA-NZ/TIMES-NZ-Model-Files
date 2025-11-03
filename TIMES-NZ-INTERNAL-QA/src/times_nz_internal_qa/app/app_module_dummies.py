"""
App processing for dummy processes
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

## Quite messy input data processing


# CONSTANTS ---------------------------------------

ID_PREFIX = "dum"


DUMMY_ENERGY_FILEPATH = FINAL_DATA / "dummy_energy.parquet"
DUMMY_DEMAND_FILEPATH = FINAL_DATA / "dummy_demand.parquet"

dummy_energy_group_options = ["Fuel", "Commodity", "Region"]
dummy_demand_group_options = [
    "SectorGroup",
    "Sector",
    "EndUse",
    "Commodity",
    "Region",
]


# define filter options. see create_filter_dict for details
# ONE PER SECTION
dummy_demand_filters = create_filter_dict(
    "dummy_demand",  # chart id for all of these
    # list of dicts
    [
        {"col": "SectorGroup", "label": "Sector Group"},
        {"col": "Sector"},
        {"col": "EndUse", "label": "End use"},
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


# Specific data processing

base_cols = ["Scenario", "Period", "Variable", "Unit"]


# GET MAIN DATA
@lru_cache(maxsize=8)
def get_dum_energy_df(scenarios, filepath=DUMMY_ENERGY_FILEPATH):
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
def get_dum_demand_df(scenarios, filepath=DUMMY_DEMAND_FILEPATH):
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


dummy_energy_parameters = {
    "page_id": ID_PREFIX,
    "chart_id": "dum_nrg",
    "sec_id": "dum-nrg",
    "filters": dummy_energy_filters,
    "section_title": "Infeasible energy",
    "base_cols": base_cols,
    "group_options": dummy_energy_group_options,
}

dummy_demand_parameters = {
    "page_id": ID_PREFIX,
    "chart_id": "dum_dem",
    "sec_id": "dum-dem",
    "filters": dummy_demand_filters,
    "section_title": "Infeasible service demand",
    "base_cols": base_cols,
    "group_options": dummy_demand_group_options,
}

# SERVER ------------------------------------------------------------------


def dummy_server(inputs, outputs, session, selected_scens):
    """
    Server functions for dummy process module
    """

    # GET DATA BASED ON SCENARIO SELECTION
    @reactive.calc
    def scen_tuple():
        """Converting scenario list to tuple. needed for hashing"""
        return tuple(selected_scens["scenario_list"]())

    register_server_functions_for_explorer(
        dummy_demand_parameters, get_dum_demand_df, scen_tuple, inputs, outputs, session
    )

    register_server_functions_for_explorer(
        dummy_energy_parameters, get_dum_energy_df, scen_tuple, inputs, outputs, session
    )


# UI --------------------------------------------------


sections = [dummy_demand_parameters, dummy_energy_parameters]


dummy_ui = make_explorer_page_ui(sections, ID_PREFIX)
