"""
Data formatting, server and ui functions for emissions data

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

# CONSTANTS -----------------------------------------------------------

ID_PREFIX = "ems"
EMS_FILE_LOCATION = FINAL_DATA / "emissions.parquet"
# define base columns that we must always group by
base_cols = [
    "Scenario",
    "Period",
    "Variable",
    "Unit",
]

# define filter options with optional labels
ems_filters_raw = [
    {"col": "SectorGroup", "label": "Sector Group"},
    {"col": "Sector"},
    # {"col": "TechnologyGroup", "label": "Technology Group"},
    {"col": "Technology"},
    # {"col": "EnduseGroup"},
    {"col": "EndUse"},
    {"col": "Region"},
    {"col": "Process"},
    # {"col": "PlantName"},
]
# build filter dict
ems_filters = create_filter_dict("emissions", ems_filters_raw)
# base group options on defined filter options
ems_group_options = [d["col"] for d in ems_filters_raw]

ems_all_group_options = base_cols + ems_group_options


# EMISSIONS DATA ----------------------------------------------------------------

# Note: want to make an electricity-specific emissions chart too for emissions by plant


@lru_cache(maxsize=8)
def get_base_ems_df(scenarios, filepath=EMS_FILE_LOCATION):
    """
    Returns emsand data (pre-filtered)
    Based on scenario selections
    Caches results for quick switching
    """
    df = read_data_pl(filepath, scenarios)
    df = df.with_columns(pl.lit("Energy emissions").alias("Variable"))
    df = aggregate_by_group(df, ems_all_group_options)
    df = df.collect()
    return df


# SERVER ----------------------------------------------------------------


def emissions_server(inputs, outputs, session, selected_scens):
    """
    server functions for electricity
    """

    # GET DATA BASED ON SCENARIO SELECTION
    @reactive.calc
    def scen_tuple():
        """Converting scenario list to tuple. needed for hashing"""
        return tuple(selected_scens["scenario_list"]())

    @reactive.calc
    def ems_df():
        return get_base_ems_df(scen_tuple())

    # make base filter options dynamic to scenario selection
    @reactive.calc
    def ems_filter_options():
        return get_filter_options_from_data(ems_df(), ems_filters)

    # REGISTER ALL FILTER FUNCTIONS FOR UI
    register_all_filters_and_clear(
        ems_filters, ems_filter_options, inputs, outputs, session
    )

    # Apply filters to data dynamically and lazily

    @reactive.calc
    def ems_df_filtered():
        group_vars = base_cols + [inputs.ems_group()]
        df = get_agg_data(ems_df(), ems_filters, inputs, group_vars)
        return df

    # Process chart inputs from filtered data
    @reactive.calc
    def ems_chart_df():
        return make_chart_data(
            ems_df_filtered(),
            base_cols,
            inputs.ems_group(),
            selected_scens["scenario_list"](),
        )

    # Render chart

    @render_altair
    def ems_chart():
        # if using altair, must touch the nav input to ensure rerendering
        _ = inputs.ems_nav()
        params = ems_chart_df()
        return build_grouped_bar(**params)

    # Generate download
    @render.download(filename="times_nz_energy_emissions.csv", media_type="text/csv")
    def ems_chart_data_download():
        yield write_polars_to_csv(ems_df())


# UI ---------------------------------------------------------------

sections = [
    (
        "ems-total",
        "Energy emissions",
        "ems_group",
        ems_group_options,
        ems_filters,
        "ems_chart",
    )
]


emissions_ui = make_explorer_page_ui(sections, ID_PREFIX)
