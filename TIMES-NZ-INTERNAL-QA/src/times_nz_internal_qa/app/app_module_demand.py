"""
Energy demand processing, ui, and server functions
"""

from functools import lru_cache

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

ID_PREFIX = "dem"

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
    {"col": "Fuel"},
    {"col": "Process"},
]

dem_filters = create_filter_dict("energy_dem", dem_filters_raw)
dem_group_options = [d["col"] for d in dem_filters_raw]

# Core variables we always group by

base_cols = [
    "Scenario",
    "Variable",
    "Period",
    "Unit",
]

dem_all_group_options = base_cols + dem_group_options


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

    # make base filter options dynamic to scenario selection
    @reactive.calc
    def dem_filter_options():
        return get_filter_options_from_data(dem_df(), dem_filters)

    # REGISTER ALL FILTER FUNCTIONS FOR UI
    register_all_filters_and_clear(
        dem_filters, dem_filter_options, inputs, outputs, session
    )

    # Apply filters to data dynamically and lazily
    @reactive.calc
    def dem_df_filtered():
        group_vars = base_cols + [inputs.dem_group()]
        df = get_agg_data(dem_df(), dem_filters, inputs, group_vars)
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

    # Render chart
    @render_altair
    def energy_dem_chart():
        # name must match sections chart_id
        # if using altair, must touch the nav input to ensure rerendering
        _ = inputs.dem_nav()
        params = dem_chart_df()
        return build_grouped_bar(**params)

    # Generate download
    @render.download(filename="times_nz_energy_end_use.csv", media_type="text/csv")
    def dem_chart_data_download():
        yield write_polars_to_csv(dem_df())


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
    )
]


demand_ui = make_explorer_page_ui(sections, ID_PREFIX)
