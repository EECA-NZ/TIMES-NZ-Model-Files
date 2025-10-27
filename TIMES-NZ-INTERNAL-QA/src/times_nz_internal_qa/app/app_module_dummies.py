"""
App processing for dummy processes
"""

from functools import lru_cache

import polars as pl
from shiny import reactive, render
from shinywidgets import render_altair
from times_nz_internal_qa.app.helpers.charts import build_grouped_bar
from times_nz_internal_qa.app.helpers.data_processing import (
    aggregate_by_group,
    get_agg_data,
    get_filter_options_from_data,
    make_chart_data,
    read_data_pl,
    write_polars_to_csv,
)
from times_nz_internal_qa.app.helpers.filters import (
    create_filter_dict,
    register_all_filters_and_clear,
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


# SERVER ------------------------------------------------------------------

# would be really good to functionalise these a bit better
# to make it easier to manage at a glance and also stop pylint complaints
# currently we re-write pretty much everything for each chart
# this goes for the ele section too


# pylint:disable = unused-argument, too-many-locals
def dummy_server(inputs, outputs, session, selected_scens):
    """
    Server functions for dummy process module
    """

    # GET DATA BASED ON SCENARIO SELECTION
    @reactive.calc
    def scen_tuple():
        """Converting scenario list to tuple. needed for hashing"""
        return tuple(selected_scens["scenario_list"]())

    @reactive.calc
    def dum_energy_df():
        return get_dum_energy_df(scen_tuple())

    @reactive.calc
    def dum_demand_df():
        return get_dum_demand_df(scen_tuple())

    # make base filter options dynamic to scenario selection
    @reactive.calc
    def dum_energy_filter_options():
        return get_filter_options_from_data(dum_energy_df(), dummy_energy_filters)

    @reactive.calc
    def dum_demand_filter_options():
        return get_filter_options_from_data(dum_demand_df(), dummy_demand_filters)

    # Register filter functions for UI
    register_all_filters_and_clear(
        dummy_demand_filters, dum_demand_filter_options, inputs, outputs, session
    )
    register_all_filters_and_clear(
        dummy_energy_filters, dum_energy_filter_options, inputs, outputs, session
    )

    # APPLY FILTERS TO DATA DYNAMICALLY

    @reactive.calc
    def dummy_energy_df_filtered():
        group_vars = base_cols + [inputs.dummy_energy_group()]
        df = get_agg_data(dum_energy_df(), dummy_energy_filters, inputs, group_vars)
        return df

    @reactive.calc
    def dummy_demand_df_filtered():
        group_vars = base_cols + [inputs.dummy_demand_group()]
        df = get_agg_data(dum_demand_df(), dummy_demand_filters, inputs, group_vars)
        return df

    # PROCESS CHART DATA

    @reactive.calc
    def dum_energy_chart_df():
        return make_chart_data(
            dummy_energy_df_filtered(),
            base_cols,
            inputs.dummy_energy_group(),
            selected_scens["scenario_list"](),
        )

    @reactive.calc
    def dum_demand_chart_df():
        return make_chart_data(
            dummy_demand_df_filtered(),
            base_cols,
            inputs.dummy_demand_group(),
            selected_scens["scenario_list"](),
        )

    # Render charts
    @render_altair
    def dummy_demand_chart():
        # if using altair, must touch the nav input to ensure rerendering
        _ = inputs.dum_nav()
        params = dum_demand_chart_df()
        return build_grouped_bar(**params)

    @render_altair
    def dummy_energy_chart():
        # if using altair, must touch the nav input to ensure rerendering
        _ = inputs.dum_nav()
        params = dum_energy_chart_df()
        return build_grouped_bar(**params)

    # Generate downloads
    @render.download(filename="times_nz_infeasible_energy.csv", media_type="text/csv")
    def dummy_energy_chart_data_download():
        yield write_polars_to_csv(dum_energy_df())

    @render.download(filename="times_nz_infeasible_demand.csv", media_type="text/csv")
    def dummy_demand_chart_data_download():
        yield write_polars_to_csv(dum_demand_df())


# UI --------------------------------------------------


sections = [
    (
        "dummy-demand",
        "Infeasible demand",
        "dummy_demand_group",
        dummy_demand_group_options,
        dummy_demand_filters,
        "dummy_demand_chart",
    ),
    (
        "dummy-energy",
        "Infeasible energy",
        "dummy_energy_group",
        dummy_energy_group_options,
        dummy_energy_filters,
        "dummy_energy_chart",
    ),
]


dummy_ui = make_explorer_page_ui(sections, ID_PREFIX)
