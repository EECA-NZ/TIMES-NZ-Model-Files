"""
App explorer page for energy service demand

Kind of a funky one since we will be using sectors that cannot be stacked

So the sector filter requires no multi options

Will need to build that into main
"""

from functools import lru_cache

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

ID_PREFIX = "esd"
ESD_FILE_LOCATION = FINAL_DATA / "energy_service_demand.parquet"


# define base columns that we must always group by
# Might even make these standard across everything?
base_cols = [
    "Scenario",
    "Variable",
    "SectorGroup",
    "Sector",
    "Period",
    "Unit",
]

# Filter options
core_filters = [
    # need to have Sector be at the top and not allow multiselect
    # have added optional multiple parameter (defaults to true)
    {"col": "Sector", "multiple": False},
    {"col": "EnduseGroup", "label": "End Use Group"},
    {"col": "EndUse", "label": "End Use"},
    {"col": "TechnologyGroup", "label": "Technology Group"},
    {"col": "Technology"},
    {"col": "Process"},
    {"col": "Region"},
]

esd_filters = create_filter_dict("esd", core_filters)

# Group options (all filters except Sector, which is in core groups)
esd_group_options = [d["col"] for d in core_filters if d["col"] != "Sector"]

esd_all_group_options = base_cols + esd_group_options


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


# SERVER ----------------------------------------------------------------


def energy_service_demand_server(inputs, outputs, session, selected_scens):
    """
    server functions for electricity
    """

    # GET DATA BASED ON SCENARIO SELECTION
    @reactive.calc
    def scen_tuple():
        """Converting scenario list to tuple. needed for hashing"""
        return tuple(selected_scens["scenario_list"]())

    @reactive.calc
    def esd_df():
        return get_base_esd_df(scen_tuple())

    # make base filter options dynamic to scenario selection
    @reactive.calc
    def esd_filter_options():
        return get_filter_options_from_data(esd_df(), esd_filters)

    # REGISTER ALL FILTER FUNCTIONS FOR UI
    register_all_filters_and_clear(
        esd_filters, esd_filter_options, inputs, outputs, session
    )

    # Apply filters to data dynamically and lazily

    @reactive.calc
    def esd_df_filtered():
        group_vars = base_cols + [inputs.esd_group()]
        df = get_agg_data(esd_df(), esd_filters, inputs, group_vars)
        return df

    # Process chart inputs from filtered data
    @reactive.calc
    def esd_chart_df():
        return make_chart_data(
            esd_df_filtered(),
            base_cols,
            inputs.esd_group(),
            selected_scens["scenario_list"](),
        )

    # Render chart

    @render_altair
    def esd_chart():
        # if using altair, must touch the nav input to ensure rerendering
        _ = inputs.esd_nav()
        params = esd_chart_df()
        return build_grouped_bar(**params)

    # Generate download
    @render.download(
        filename="times_nz_energy_service_demand.csv", media_type="text/csv"
    )
    def esd_chart_data_download():
        yield write_polars_to_csv(esd_df())


# UI ---------------------------------------------------------------

sections = [
    (
        "esd-total",
        "Energy service demand",
        "esd_group",
        esd_group_options,
        esd_filters,
        "esd_chart",
    )
]


esd_ui = make_explorer_page_ui(sections, ID_PREFIX)
