"""
Data formatting, server and ui functions for electricity generation data

"""

from functools import lru_cache

import polars as pl
from shiny import reactive, render
from shinywidgets import render_altair
from times_nz_internal_qa.app.helpers.charts import (
    build_grouped_bar,
)
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

ele_all_group_options = ele_base_cols + ele_core_group_options + ["Fuel"]


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


# pylint:disable = too-many-locals, unused-argument
def elec_server(inputs, outputs, session, selected_scens):
    """
    server functions for electricity
    """

    @reactive.calc
    def scen_tuple():
        """Converting scenario list to tuple. needed for hashing"""
        return tuple(selected_scens["scenario_list"]())

    # Many of the next steps come in groups of three - one for each chart currently built

    # Possibly could stand to make more factories here instead, especially if we want more charts.

    # get each table for each chart
    @reactive.calc
    def ele_gen_df():
        return get_base_ele_gen_df(scen_tuple())

    @reactive.calc
    def ele_cap_df():
        return get_base_ele_cap_df(scen_tuple())

    @reactive.calc
    def ele_use_df():
        return get_base_ele_use_df(scen_tuple())

    # separately, take base filter options data

    @reactive.calc
    def ele_gen_filter_options():
        return get_filter_options_from_data(ele_gen_df(), ele_gen_filters)

    @reactive.calc
    def ele_cap_filter_options():
        return get_filter_options_from_data(ele_cap_df(), ele_cap_filters)

    @reactive.calc
    def ele_use_filter_options():
        return get_filter_options_from_data(ele_use_df(), ele_use_filters)

    # register all filter controls for server side maintenance

    register_all_filters_and_clear(
        ele_gen_filters, ele_gen_filter_options, inputs, outputs, session
    )
    register_all_filters_and_clear(
        ele_cap_filters, ele_cap_filter_options, inputs, outputs, session
    )
    register_all_filters_and_clear(
        ele_use_filters, ele_use_filter_options, inputs, outputs, session
    )

    # APPLY FILTERS TO DATA DYNAMICALLY AND LAZILY
    @reactive.calc
    def ele_cap_df_filtered():
        group_vars = ele_base_cols + [inputs.ele_cap_group()]
        df = get_agg_data(ele_cap_df(), ele_cap_filters, inputs, group_vars)
        return df

    @reactive.calc
    def ele_use_df_filtered():
        group_vars = ele_base_cols + [inputs.ele_use_group()]
        df = get_agg_data(ele_use_df(), ele_use_filters, inputs, group_vars)
        return df

    @reactive.calc
    def ele_gen_df_filtered():
        group_vars = ele_base_cols + [inputs.ele_gen_group()]
        df = get_agg_data(ele_gen_df(), ele_gen_filters, inputs, group_vars)
        return df

    # CREATE CHART OUTPUT DATA
    @reactive.calc
    def ele_gen_chart_df():
        return make_chart_data(
            ele_gen_df_filtered(),
            ele_base_cols,
            inputs.ele_gen_group(),
            selected_scens["scenario_list"](),
        )

    @reactive.calc
    def ele_cap_chart_df():
        return make_chart_data(
            ele_cap_df_filtered(),
            ele_base_cols,
            inputs.ele_cap_group(),
            selected_scens["scenario_list"](),
        )

    @reactive.calc
    def ele_use_chart_df():
        return make_chart_data(
            ele_use_df_filtered(),
            ele_base_cols,
            inputs.ele_use_group(),
            selected_scens["scenario_list"](),
        )

    # DRAW CHARTS
    @render_altair
    def ele_gen_chart():
        # if using altair, must touch the nav input to ensure rerendering
        _ = inputs.elec_nav()
        params = ele_gen_chart_df()
        return build_grouped_bar(**params)

    @render_altair
    def ele_cap_chart():
        # if using altair, must touch the nav input to ensure rerendering
        _ = inputs.elec_nav()
        params = ele_cap_chart_df()
        return build_grouped_bar(**params)

    @render_altair
    def ele_use_chart():
        # if using altair, must touch the nav input to ensure rerendering
        # this can be skipped if using plotly
        _ = inputs.elec_nav()
        params = ele_use_chart_df()
        return build_grouped_bar(**params)

    # CSV downloads (not yet functionalised sorry)
    @render.download(
        filename="times_nz_electricity_generation.csv", media_type="text/csv"
    )
    def ele_gen_chart_data_download():
        yield write_polars_to_csv(ele_gen_df())

    @render.download(
        filename="times_nz_electricity_fuel_use.csv", media_type="text/csv"
    )
    def ele_use_chart_data_download():
        yield write_polars_to_csv(ele_use_df())

    @render.download(
        filename="times_nz_electricity_generation_capacity.csv", media_type="text/csv"
    )
    def ele_cap_chart_data_download():
        yield write_polars_to_csv(ele_cap_df())


# UI ------------------------------------------------


sections = [
    (
        "elec-gen",
        "Electricity generation",
        "ele_gen_group",
        ele_core_group_options,
        ele_gen_filters,
        "ele_gen_chart",
    ),
    (
        "elec-use",
        "Fuel used for generation",
        "ele_use_group",
        ele_core_group_options + ["Fuel"],
        ele_use_filters,
        "ele_use_chart",
    ),
    (
        "elec-cap",
        "Generation capacity",
        "ele_cap_group",
        ele_core_group_options,
        ele_cap_filters,
        "ele_cap_chart",
    ),
]

elec_ui = make_explorer_page_ui(sections, ID_PREFIX)
