"""
Energy production server and ui
"""

from functools import lru_cache

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

# CONSTANTS --------------------------------------------------

# all modules get a unique id code to generate other IDs with
ID_PREFIX = "prd"

PRI_FILE_LOCATION = FINAL_DATA / "primary_energy.parquet"

# SET FILTER/GROUP OPTIONS

pri_filters = [
    {"col": "ProcessGroup", "label": "Sector Group"},
    {"col": "ProcessName"},
    {"col": "Process"},
    {"col": "Fuel"},
]

# we add fuel to main

pri_filters = create_filter_dict("prd", pri_filters)


pri_group_options = [d["col"] for d in pri_filters]

# Core variables we always group by

base_cols = [
    "Scenario",
    "Variable",
    "Period",
    "Unit",
]

pri_all_group_options = base_cols + pri_group_options


# SET PARAMETERS

pri_parameters = {
    "page_id": ID_PREFIX,
    "chart_id": "energy_prod",
    "sec_id": "energy-prod",
    "filters": pri_filters,
    "section_title": "Primary energy production",
    "base_cols": base_cols,
    "group_options": pri_group_options,
}


# GET DATA ------------------------------------------


@lru_cache(maxsize=8)
def get_base_pri_df(scenarios, filepath=PRI_FILE_LOCATION):
    """
    Returns demand data (pre-filtered)
    Based on scenario selections
    Caches results for quick switching
    """
    df = read_data_pl(filepath, scenarios)
    df = aggregate_by_group(df, pri_all_group_options)
    df = df.collect()
    return df


# SERVER ------------------------------------------


# pylint:disable = too-many-locals, unused-argument, too-many-statements
def pri_server(inputs, outputs, session, selected_scens):
    """
    Server functions for energy demand module
    """

    @reactive.calc
    def scen_tuple():
        """Converting scenario list to tuple. needed for hashing"""
        return tuple(selected_scens["scenario_list"]())

    register_server_functions_for_explorer(
        pri_parameters, get_base_pri_df, scen_tuple, inputs, outputs, session
    )


# UI --------------------------------------------


sections = [pri_parameters]


primary_energy_ui = make_explorer_page_ui(sections, ID_PREFIX)
