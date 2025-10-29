"""
Energy demand processing, ui, and server functions
"""

from functools import lru_cache

import polars as pl
from shiny import reactive, render
from shinywidgets import render_altair
from times_nz_internal_qa.app.helpers.charts import build_grouped_bar
from times_nz_internal_qa.app.helpers.data_processing import (
    aggregate_by_group,
    filter_df_for_variable,
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

# CONSTANTS --------------------------------------------------

# all modules get a unique id code to generate other IDs with
ID_PREFIX = "dem"

PJ_TO_GWH = 277.778
DEM_FILE_LOCATION = FINAL_DATA / "energy_demand.parquet"

# SET FILTER/GROUP OPTIONS

dem_filters_raw = [
    {"col": "SectorGroup", "label": "Sector Group"},
    {"col": "Sector"},
    # {"col": "TechnologyGroup", "label": "Technology Group"},
    {"col": "Technology"},
    # {"col": "EnduseGroup"},
    {"col": "EndUse"},
    {"col": "Region"},
    {"col": "Process"},
]

# we add fuel to main
dem_filters = dem_filters_raw + [{"col": "Fuel"}]
dem_filters = create_filter_dict("energy_dem", dem_filters)
elc_dem_filters = create_filter_dict("elc_dem", dem_filters_raw)

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

    # GET BASE DEMAND DATA

    @reactive.calc
    def dem_df():
        return get_base_dem_df(scen_tuple())

    @reactive.calc
    def elc_dem_df():
        return get_base_elc_dem_df(scen_tuple())

    # make base filter options dynamic to scenario selection
    @reactive.calc
    def dem_filter_options():
        return get_filter_options_from_data(dem_df(), dem_filters)

    @reactive.calc
    def elc_dem_filter_options():
        return get_filter_options_from_data(elc_dem_df(), elc_dem_filters)

    # REGISTER ALL FILTER FUNCTIONS FOR UI
    register_all_filters_and_clear(
        dem_filters, dem_filter_options, inputs, outputs, session
    )

    register_all_filters_and_clear(
        elc_dem_filters, elc_dem_filter_options, inputs, outputs, session
    )

    # Apply filters to data dynamically and lazily
    @reactive.calc
    def dem_df_filtered():
        group_vars = base_cols + [inputs.dem_group()]
        df = get_agg_data(dem_df(), dem_filters, inputs, group_vars)
        return df

    @reactive.calc
    def elc_dem_df_filtered():
        group_vars = base_cols + [inputs.elc_dem_group()]
        df = get_agg_data(elc_dem_df(), elc_dem_filters, inputs, group_vars)
        return df

    # process chart inputs from filtered data
    @reactive.calc
    def dem_chart_df():
        return make_chart_data(
            dem_df_filtered(),
            base_cols,
            inputs.dem_group(),
            selected_scens["scenario_list"](),
        )

    @reactive.calc
    def elc_dem_chart_df():
        return make_chart_data(
            elc_dem_df_filtered(),
            base_cols,
            inputs.elc_dem_group(),
            selected_scens["scenario_list"](),
        )

    # Render chart
    @render_altair
    def energy_dem_chart():
        # name must match sections chart_id
        # if using altair, must touch the nav input to ensure rerendering
        _ = inputs.dem_nav()
        params = dem_chart_df()
        return build_grouped_bar(**params)

    @render_altair
    def elc_dem_chart():
        # name must match sections chart_id
        # if using altair, must touch the nav input to ensure rerendering
        _ = inputs.dem_nav()
        params = elc_dem_chart_df()
        return build_grouped_bar(**params)

    # Generate download
    @render.download(filename="times_nz_energy_end_use.csv", media_type="text/csv")
    def energy_dem_chart_data_download():
        yield write_polars_to_csv(dem_df())

    @render.download(filename="times_nz_electricity_end_use.csv", media_type="text/csv")
    def elc_dem_chart_data_download():
        yield write_polars_to_csv(elc_dem_df())


# UI --------------------------------------------


sections = [
    # single section for a single chart
    (
        "dem-total",
        "Total energy demand",
        "dem_group",
        dem_group_options,
        dem_filters,
        "energy_dem_chart",
    ),
    (
        "elc-dem",
        "Electricity demand",
        "elc_dem_group",
        elc_dem_group_options,
        elc_dem_filters,
        "elc_dem_chart",
    ),
]


demand_ui = make_explorer_page_ui(sections, ID_PREFIX)
