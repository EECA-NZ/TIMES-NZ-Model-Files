"""
Data formatting, server and ui functions for electricity generation data

"""

import altair as alt
import numpy as np
import pandas as pd
from shiny import reactive, render, ui
from shinywidgets import output_widget, render_altair
from times_nz_internal_qa.utilities.data_formatting import (
    complete_periods,
    get_df_options,
)
from times_nz_internal_qa.utilities.filepaths import FINAL_DATA

# define base columns that we must always group by
base_cols = [
    "Scenario",
    "Attribute",
    "Variable",
    "Period",
    "Unit",
]


def get_ele_gen_df():
    """
    Formatting for electricity generation. Outputs the main data ready for web ingestion
    Also outputs a variable/unit map for web processing

    """

    df = pd.read_csv(FINAL_DATA / "elec_generation.csv", low_memory=False)
    df = df.fillna("-")

    cols = [
        "Scenario",
        "Attribute",
        "Variable",
        "PlantName",
        "TechnologyGroup",
        "Technology",
        "Fuel",
        "Region",
        "Period",
        "Unit",
    ]

    df = df.groupby(cols)["Value"].sum().reset_index()

    # convert output to GWh
    df["Value"] = np.where(
        df["Variable"] == "Electricity generation",
        df["Value"] * 277.78,
        df["Value"],
    )
    df["Unit"] = np.where(df["Variable"] == "Electricity generation", "GWh", df["Unit"])

    df_unit_map = df.set_index("Variable")["Unit"].to_dict()

    return df, df_unit_map


# would prefer to handle these a little less messy - please refactor
ele_gen_df, unit_map = get_ele_gen_df()

ele_gen_variables = get_df_options(ele_gen_df, "Variable")

ele_gen_group_options = [
    "TechnologyGroup",
    "Region",
    "PlantName",
    "Technology",
    "PlantName",
    "Fuel",
]


# pylint:disable = too-many-locals, unused-argument
def elec_server(inputs, outputs, session):
    """
    server functions for electricity
    """

    # electricity generation data
    @reactive.calc
    def df_elec():
        df = ele_gen_df
        df = df[df["Variable"] == inputs.variable()]

        return df

    @reactive.calc
    def df_elec_filtered():
        d = df_elec()
        # tech
        if inputs.tech_filter():
            d = d[d["Technology"].astype(str).isin(inputs.tech_filter())]
        # tech group
        if inputs.techgroup_filter():
            d = d[d["TechnologyGroup"].astype(str).isin(inputs.techgroup_filter())]
        # island
        if inputs.island_filter():
            d = d[d["Region"].astype(str).isin(inputs.island_filter())]
        # specific plant
        if inputs.plant_filter():
            d = d[d["PlantName"].astype(str).isin(inputs.plant_filter())]

        if inputs.fuel_filter():
            d = d[d["Fuel"].astype(str).isin(inputs.fuel_filter())]
        return d

    @reactive.calc
    def df_elec_techgroup_filtered():
        d = df_elec().copy()
        if inputs.techgroup_filter():
            d = d[d["TechnologyGroup"].astype(str).isin(inputs.techgroup_filter())]
        return d

    def df_elec_tech_filtered():
        d = df_elec().copy()
        if inputs.techgroup_filter():
            d = d[d["TechnologyGroup"].astype(str).isin(inputs.techgroup_filter())]
        if inputs.tech_filter():
            d = d[d["Technology"].astype(str).isin(inputs.tech_filter())]
        return d

    # current filter options

    @outputs
    @render.ui
    def techgroup_filters():
        d = df_elec()
        tech_group_choices = get_df_options(d, "TechnologyGroup")
        return (
            ui.input_selectize(
                "techgroup_filter", "TechnologyGroup", tech_group_choices, multiple=True
            ),
        )

    @outputs
    @render.ui
    def tech_filters():
        d = df_elec_techgroup_filtered()
        tech_choices = get_df_options(d, "Technology")
        return (
            ui.input_selectize(
                "tech_filter", "Technology", tech_choices, multiple=True
            ),
        )

    @outputs
    @render.ui
    def island_filters():
        df = df_elec()
        island_choices = get_df_options(df, "Region")
        return (
            ui.input_selectize(
                "island_filter", "Region", island_choices, multiple=True
            ),
        )

    @outputs
    @render.ui
    def plant_filters():
        df = df_elec_tech_filtered()
        plant_choices = get_df_options(df, "PlantName")
        return (
            ui.input_selectize(
                "plant_filter", "PlantName", plant_choices, multiple=True
            ),
        )

    @outputs
    @render.ui
    def fuel_filters():
        df = df_elec_tech_filtered()
        fuel_choices = get_df_options(df, "Fuel")
        return (ui.input_selectize("fuel_filter", "Fuel", fuel_choices, multiple=True),)

    @outputs
    @render.ui
    def ele_filters():
        return ui.layout_columns(
            ui.output_ui("techgroup_filters"),
            ui.output_ui("tech_filters"),
            ui.output_ui("island_filters"),
            ui.output_ui("plant_filters"),
            ui.output_ui("fuel_filters"),
        )

    # GROUPING
    @reactive.calc
    def df_elec_grouped():
        d = df_elec_filtered()
        return d.groupby(base_cols + [inputs.group()])["Value"].sum().reset_index()

    # GENERATE TITLE

    @reactive.calc
    def elec_chart_title_text():
        var = inputs.variable()
        grp = inputs.group()

        return f"{var} by {grp}"

    @outputs
    @render.ui
    def elec_chart_title():
        return ui.h3(elec_chart_title_text())

    # CHART
    @outputs(id="elec_chart")
    @render_altair
    def _():
        d = df_elec_grouped()
        dc = complete_periods(
            d,
            period_list=range(2023, 2051),
            # base cols but not period
            category_cols=[
                "Scenario",
                "Attribute",
                "Variable",
                # "Period",
                "Unit",
            ]
            + [inputs.group()],
        )

        var = inputs.variable()
        unit = unit_map.get(var, "")
        return (
            alt.Chart(dc)
            .mark_bar(size=50, opacity=0.85)
            .encode(
                x=alt.X("Period:N", title="Year"),
                y=alt.Y("Value:Q", title=f"{unit}"),
                color=f"{inputs.group()}:N",
                tooltip=[
                    # alt.Tooltip("PlantName:N", title=""),
                    alt.Tooltip(f"{inputs.group()}:N", title=inputs.group()),
                    alt.Tooltip("Value:Q", title=f"{unit}", format=",.2f"),
                    # alt.Tooltip("y:Q", title="Y", format=",.2f"),
                ],
            )
        )

    # DOWNLOAD

    @outputs
    @render.download(filename="electricity_data.csv")
    def download_elec_data():
        # yield file chunks to the client
        with open(FINAL_DATA / "elec_generation.csv", "rb") as f:
            yield from f


elec_ui = ui.page_fluid(
    # ele generation
    ui.row(
        ui.column(6, ui.output_ui("elec_chart_title")),
        ui.column(
            2,
            ui.input_select(
                "variable",
                "Select variable",
                ele_gen_variables,
                selected=ele_gen_variables[0],
            ),
        ),
        ui.column(2, ui.input_select("group", "Group by:", ele_gen_group_options)),
        ui.column(
            2,
            ui.download_button("download_elec_data", "Download raw data"),
            style="width:10%;min-width:240px;",
        ),
    ),
    ui.span("Filters"),
    ui.output_ui("ele_filters"),
    output_widget("elec_chart"),
)
