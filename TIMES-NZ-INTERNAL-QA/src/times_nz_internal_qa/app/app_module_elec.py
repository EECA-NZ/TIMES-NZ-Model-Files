"""
Data formatting, server and ui functions for electricity generation data

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

# CONSTANTS  ------------------------------------------------------------------------------


# ID_PREFIX is used to ensure some ui and server elements link correctly
ID_PREFIX = "elec"

# define base columns that we must always group by
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

fuel_filters = [
    {"col": "Fuel"},
]

ele_gen_filters = create_filter_dict("ele_gen", core_filters)
ele_cap_filters = create_filter_dict("ele_cap", core_filters)
ele_use_filters = create_filter_dict("ele_use", core_filters + fuel_filters)

# PROCESS DATA


def get_base_ele_df():
    """Minor tidying of the base input"""

    df = pd.read_parquet(FINAL_DATA / "elec_generation.parquet")
    df = df.fillna("-")
    df["Period"] = df["Period"].astype(int)

    return df


def get_ele_gen_data(df, variable):
    """
    Filter for the variable we want to display
    Convert PJ to GWh for output
    """
    df = df[df["Variable"] == variable].copy()
    if variable == "Electricity generation":
        df["Value"] = df["Value"] * 277.78
        df["Unit"] = "GWh"
    return df


base_df = get_base_ele_df()


# pylint:disable = too-many-locals, unused-argument
def elec_server(inputs, outputs, session, selected_scens):
    """
    server functions for electricity
    """

    # filter on scenarios
    @reactive.calc
    def base_df_scens():
        """
        Filter raw data for the scenario list
        """
        d = base_df.copy()
        d = d[d["Scenario"].isin(selected_scens["scenario_list"]())]
        return d

    # get each table for each chart
    @reactive.calc
    def ele_gen_df():
        return get_ele_gen_data(base_df_scens(), "Electricity generation")

    @reactive.calc
    def ele_cap_df():
        return get_ele_gen_data(base_df_scens(), "Electricity generation capacity")

    @reactive.calc
    def ele_use_df():
        return get_ele_gen_data(base_df_scens(), "Electricity fuel use")

    # REGISTER ALL FILTER FUNCTIONS FOR UI
    # Currently we do this once per chart
    for fs in ele_gen_filters:
        register_filter_from_factory(
            fs, ele_gen_df, ele_gen_filters, inputs, outputs, session
        )

    for fs in ele_cap_filters:
        register_filter_from_factory(
            fs, ele_cap_df, ele_cap_filters, inputs, outputs, session
        )

    for fs in ele_use_filters:
        register_filter_from_factory(
            fs, ele_use_df, ele_use_filters, inputs, outputs, session
        )

    # APPLY FILTERS TO DATA DYNAMICALLY (group afterwards)
    @reactive.calc
    def ele_cap_df_filtered():
        d = ele_cap_df().copy()
        d = apply_filters(d, ele_cap_filters, inputs)
        return (
            d.groupby(ele_base_cols + [inputs.ele_cap_group()])["Value"]
            .sum()
            .reset_index()
        )

    @reactive.calc
    def ele_use_df_filtered():
        d = ele_use_df().copy()
        d = apply_filters(d, ele_use_filters, inputs)
        return (
            d.groupby(ele_base_cols + [inputs.ele_use_group()])["Value"]
            .sum()
            .reset_index()
        )

    @reactive.calc
    def ele_gen_df_filtered():
        d = ele_gen_df().copy()
        d = apply_filters(d, ele_gen_filters, inputs)
        return (
            d.groupby(ele_base_cols + [inputs.ele_gen_group()])["Value"]
            .sum()
            .reset_index()
        )

    # CHARTS
    @outputs(id="ele_gen_chart")
    @render_altair
    def _():

        return build_grouped_bar(
            ele_gen_df_filtered(),
            ele_base_cols,
            inputs.ele_gen_group(),
            selected_scens["scenario_list"](),
        )

    @outputs(id="ele_use_chart")
    @render_altair
    def _():
        return build_grouped_bar(
            ele_use_df_filtered(),
            ele_base_cols,
            inputs.ele_use_group(),
            selected_scens["scenario_list"](),
        )

    @outputs(id="ele_cap_chart")  # reminder: this is the section's chart_id
    @render_altair
    def _():
        return build_grouped_bar(
            ele_cap_df_filtered(),
            ele_base_cols,
            inputs.ele_cap_group(),
            selected_scens["scenario_list"](),
        )

    # CSV downloads (not yet functionalised sorry)
    @render.download(filename="ele_gen_chart_data_download.csv", media_type="text/csv")
    def ele_gen_chart_data_download():
        buf = io.StringIO()
        ele_gen_df_filtered().to_csv(buf, index=False)
        yield buf.getvalue()

    @render.download(filename="ele_use_chart_data_download.csv", media_type="text/csv")
    def ele_use_chart_data_download():
        buf = io.StringIO()
        ele_use_df_filtered().to_csv(buf, index=False)
        yield buf.getvalue()

    @render.download(filename="ele_cap_chart_data_download.csv", media_type="text/csv")
    def ele_cap_chart_data_download():
        buf = io.StringIO()
        ele_cap_df_filtered().to_csv(buf, index=False)
        yield buf.getvalue()

    @render.download(filename="ele_gen_data_raw.csv", media_type="text/csv")
    def ele_all_data_download():
        buf = io.StringIO()
        base_df.to_csv(buf, index=False)
        yield buf.getvalue()


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
