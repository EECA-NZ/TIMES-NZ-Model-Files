"""
Energy demand processing, ui, and server functions
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

# CONSTANTS --------------------------------------------------

ID_PREFIX = "dem"

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

# GET DATA ------------------------------------------


def get_energy_dem():
    """
    Formatting for all energy demand. Outputs the main data ready for web ingestion
    """

    df = pd.read_parquet(FINAL_DATA / "energy_demand.parquet")
    df = df.fillna("-")
    df["Period"] = df["Period"].astype("Int64")
    return df


energy_dem_base_df = get_energy_dem()


# SERVER ------------------------------------------


# pylint:disable = too-many-locals, unused-argument, too-many-statements
def demand_server(inputs, outputs, session, selected_scens):
    """
    Server functions for energy demand module
    """

    @reactive.calc
    def energy_dem_df():
        """
        Filter raw data for the scenario list
        """
        d = energy_dem_base_df.copy()
        d = d[d["Scenario"].isin(selected_scens["scenario_list"]())]
        return d

    # REGISTER ALL FILTER FUNCTIONS FOR UI
    for fs in dem_filters:
        register_filter_from_factory(
            fs, energy_dem_df, dem_filters, inputs, outputs, session
        )

    # DYNAMICALLY FILTER/GROUP DATA

    @reactive.calc
    def energy_dem_df_filtered():
        d = energy_dem_df().copy()
        d = apply_filters(d, dem_filters, inputs)
        return d.groupby(base_cols + [inputs.dem_group()])["Value"].sum().reset_index()

    # Render chart

    @outputs(id="dem_chart")
    @render_altair
    def _():
        return build_grouped_bar(
            energy_dem_df_filtered(),
            base_cols,
            inputs.dem_group(),
            scen_list=selected_scens["scenario_list"](),
        )

    # Generate downloads
    @render.download(filename="dem_chart_data_download.csv", media_type="text/csv")
    def dem_chart_data_download():
        buf = io.StringIO()
        energy_dem_df_filtered().to_csv(buf, index=False)
        yield buf.getvalue()

    @render.download(filename="dem_data_raw.csv", media_type="text/csv")
    def dem_all_data_download():
        buf = io.StringIO()
        energy_dem_base_df.to_csv(buf, index=False)
        yield buf.getvalue()


# UI --------------------------------------------


sections = [
    # single section for a single chart
    (
        "dem-total",
        "Total energy demand",
        "dem_group",
        dem_group_options,
        dem_filters,
        "dem_chart",
    )
]


demand_ui = make_explorer_page_ui(sections, ID_PREFIX)
