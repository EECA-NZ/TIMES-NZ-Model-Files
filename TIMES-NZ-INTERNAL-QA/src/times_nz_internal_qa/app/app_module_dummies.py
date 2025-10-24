"""
App processing for dummy processes
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

## Quite messy input data processing

dummy_energy_raw = pd.read_parquet(FINAL_DATA / "dummy_energy.parquet")
dummy_demand_raw = pd.read_parquet(FINAL_DATA / "dummy_demand.parquet")


# CONSTANTS ---------------------------------------

ID_PREFIX = "dum"

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


# GET MAIN DATA
def get_df_dummy(df):
    """Small preprocessing for dummy data"""
    df["Period"] = df["Period"].astype("Int64")
    df["Unit"] = "PJ"  # not always true but fine for placeholder
    return df


base_cols = ["Scenario", "Period", "Unit"]

# SERVER ------------------------------------------------------------------


# pylint:disable = unused-argument
def dummy_server(inputs, outputs, session, selected_scens):
    """
    Server functions for dummy process module
    """
    # GET DATA BASED ON SCENARIO SELECTION

    df_dummy_demand_base = get_df_dummy(dummy_demand_raw)
    df_dummy_energy_base = get_df_dummy(dummy_energy_raw)

    @reactive.calc
    def df_dummy_demand():
        """
        Filter raw data for the scenario list
        """
        d = df_dummy_demand_base.copy()
        d = d[d["Scenario"].isin(selected_scens["scenario_list"]())]
        return d

    @reactive.calc
    def df_dummy_energy():
        """
        Filter raw data for the scenario list
        """
        d = df_dummy_energy_base.copy()
        d = d[d["Scenario"].isin(selected_scens["scenario_list"]())]
        return d

    # REGISTER ALL FILTER FUNCTIONS FOR UI
    for fs in dummy_demand_filters:
        register_filter_from_factory(
            fs, df_dummy_demand, dummy_demand_filters, inputs, outputs, session
        )

    for fs in dummy_energy_filters:
        register_filter_from_factory(
            fs, df_dummy_energy, dummy_energy_filters, inputs, outputs, session
        )

    # APPLY FILTERS TO DATA DYNAMICALLY
    @reactive.calc
    def df_dummy_demand_filtered():
        d = df_dummy_demand().copy()
        return apply_filters(d, dummy_demand_filters, inputs)

    @reactive.calc
    def df_dummy_energy_filtered():
        d = df_dummy_energy().copy()
        return apply_filters(d, dummy_energy_filters, inputs)

    # APPPLY DYNAMIC GROUPING AFTER FILTERING
    @reactive.calc
    def dummy_demand_grouped():
        d = df_dummy_demand_filtered()
        return (
            d.groupby(base_cols + [inputs.dummy_demand_group()])["Value"]
            .sum()
            .reset_index()
        )

    @reactive.calc
    def dummy_energy_grouped():
        d = df_dummy_energy_filtered()
        return (
            d.groupby(base_cols + [inputs.dummy_energy_group()])["Value"]
            .sum()
            .reset_index()
        )

    # RENDER CHARTS
    @outputs(id="dummy_demand_chart")
    @render_altair
    def _():
        return build_grouped_bar(
            dummy_demand_grouped(),
            base_cols,
            inputs.dummy_demand_group(),
            scen_list=selected_scens["scenario_list"](),
        )

    @outputs(id="dummy_energy_chart")
    @render_altair
    def _():
        return build_grouped_bar(
            dummy_energy_grouped(),
            base_cols,
            inputs.dummy_energy_group(),
            scen_list=selected_scens["scenario_list"](),
        )

    # DOWNLOADS
    @render.download(filename="df_dummy_demand.csv", media_type="text/csv")
    def dummy_demand_chart_data_download():
        buf = io.StringIO()
        df_dummy_demand.to_csv(buf, index=False)
        yield buf.getvalue()

    @render.download(filename="df_dummy_energy.csv", media_type="text/csv")
    def dummy_energy_chart_data_download():
        buf = io.StringIO()
        df_dummy_energy.to_csv(buf, index=False)
        yield buf.getvalue()


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
