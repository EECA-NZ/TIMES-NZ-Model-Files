"""
Data formatting, server and ui functions for emissions data

"""

import io

import pandas as pd
from shiny import reactive, render
from shinywidgets import render_altair
from times_nz_internal_qa.app.helpers.charts import build_grouped_bar
from times_nz_internal_qa.app.helpers.filters import (
    apply_filters,
    create_filter_dict,
    register_filter_from_factory,
)
from times_nz_internal_qa.app.helpers.ui_elements import make_explorer_page_ui
from times_nz_internal_qa.utilities.filepaths import FINAL_DATA

# CONSTANTS

ID_PREFIX = "ems"
# define base columns that we must always group by
base_cols = [
    "Scenario",
    "Period",
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


# DATA PROCESSING
def get_emissions_df():
    """
    Formatting for emissions. Very minor handling
    """

    df = pd.read_parquet(FINAL_DATA / "emissions.parquet")
    df["Period"] = df["Period"].astype(int)

    df = df.fillna("-")
    return df


# pylint:disable = too-many-locals, unused-argument
def emissions_server(inputs, outputs, session, selected_scens):
    """
    server functions for electricity
    """

    # GET DATA BASED ON SCENARIO SELECTION
    emissions_df = get_emissions_df()

    @reactive.calc
    def emissions_df_scens():
        """
        Filter raw data for the scenario list
        """
        d = emissions_df.copy()
        d = d[d["Scenario"].isin(selected_scens["scenario_list"]())]
        return d

    # Register all filters
    for fs in ems_filters:
        register_filter_from_factory(
            fs, emissions_df_scens, ems_filters, inputs, outputs, session
        )

    # dynamically filter data
    @reactive.calc
    def emissions_df_filtered():
        d = emissions_df_scens().copy()
        d = apply_filters(d, ems_filters, inputs)
        return d.groupby(base_cols + [inputs.ems_group()])["Value"].sum().reset_index()

    # CHART
    @outputs(id="ems_chart")
    @render_altair
    def _():
        return build_grouped_bar(
            emissions_df_filtered(),
            base_cols,
            inputs.ems_group(),
            scen_list=selected_scens["scenario_list"](),
        )

    # DOWNLOADS
    # Generate download
    @render.download(filename="ems_chart_data_download.csv", media_type="text/csv")
    def ems_chart_data_download():
        buf = io.StringIO()
        emissions_df_filtered().to_csv(buf, index=False)
        yield buf.getvalue()

    @render.download(filename="ems_data_raw.csv", media_type="text/csv")
    def ems_all_data_download():
        buf = io.StringIO()
        emissions_df.to_csv(buf, index=False)
        yield buf.getvalue()


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
