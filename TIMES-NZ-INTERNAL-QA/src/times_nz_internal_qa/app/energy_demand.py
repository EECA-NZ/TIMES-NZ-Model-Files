"""
Energy demand processing, ui, and server functions
"""

import altair as alt
import pandas as pd
from shiny import reactive, render, ui
from shinywidgets import output_widget, render_altair
from times_nz_internal_qa.utilities.data_formatting import (
    complete_periods,
    get_df_options,
)
from times_nz_internal_qa.utilities.filepaths import FINAL_DATA

# helpers


def get_energy_demand():
    """
    Formatting for all energy demand. Outputs the main data ready for web ingestion
    """

    df = pd.read_csv(FINAL_DATA / "energy_demand.csv", low_memory=False)
    df = df.fillna("-")
    cols = [
        "Scenario",
        "Attribute",
        "Variable",
        "SectorGroup",
        "Sector",
        "TechnologyGroup",
        "Technology",
        "EnduseGroup",
        "EndUse",
        "CommodityGroup",
        "Fuel",
        "Region",
        "Period",
        "Process",
        "Unit",
    ]
    df = df.groupby(cols)["Value"].sum().reset_index()

    return df


demand_group_options = [
    "SectorGroup",
    "Sector",
    "TechnologyGroup",
    "Technology",
    "EnduseGroup",
    "EndUse",
    "CommodityGroup",
    "Fuel",
    "Region",
    "Process",
]


# pylint:disable = too-many-locals, unused-argument, too-many-statements
def demand_server(inputs, outputs, session):
    """
    Server functions for energy demand module
    """

    base_cols = [
        "Scenario",
        "Attribute",
        "Variable",
        "Period",
        "Unit",
    ]

    @reactive.calc
    def demand_chart_title_text():

        grp = inputs.demand_group()

        return f"Energy demand by {grp}"

    @outputs
    @render.ui
    def energy_demand_title():
        return ui.h3(demand_chart_title_text())

    df_energy_demand = get_energy_demand()

    # FILTER SELECTIONS
    @outputs
    @render.ui
    def demand_sector_group_filters():
        d = df_energy_demand
        choices = get_df_options(d, "SectorGroup")
        return (
            ui.input_selectize(
                "demand_sector_group_filter", "SectorGroup", choices, multiple=True
            ),
        )

    @outputs
    @render.ui
    def demand_sector_filters():
        d = df_demand_sector_group_filtered()
        choices = get_df_options(d, "Sector")
        return (
            ui.input_selectize(
                "demand_sector_filter", "Sector", choices, multiple=True
            ),
        )

    @outputs
    @render.ui
    def demand_tech_group_filters():
        d = df_energy_demand
        choices = get_df_options(d, "TechnologyGroup")
        return (
            ui.input_selectize(
                "demand_tech_group_filter", "TechnologyGroup", choices, multiple=True
            ),
        )

    @outputs
    @render.ui
    def demand_tech_filters():
        d = df_energy_demand
        choices = get_df_options(d, "Technology")
        return (
            ui.input_selectize(
                "demand_tech_filter", "Technology", choices, multiple=True
            ),
        )

    @outputs
    @render.ui
    def demand_enduse_group_filters():
        d = df_demand_tech_group_filtered()
        choices = get_df_options(d, "EnduseGroup")
        return (
            ui.input_selectize(
                "demand_enduse_group_filter", "EnduseGroup", choices, multiple=True
            ),
        )

    @outputs
    @render.ui
    def demand_enduse_filters():
        d = df_demand_enduse_group_filtered()
        choices = get_df_options(d, "EndUse")
        return (
            ui.input_selectize(
                "demand_enduse_filter", "EndUse", choices, multiple=True
            ),
        )

    @outputs
    @render.ui
    def demand_fuel_filters():
        d = df_energy_demand
        choices = get_df_options(d, "Fuel")
        return (
            ui.input_selectize("demand_fuel_filter", "Fuel", choices, multiple=True),
        )

    @outputs
    @render.ui
    def demand_region_filters():
        d = df_energy_demand
        choices = get_df_options(d, "Region")
        return (
            ui.input_selectize(
                "demand_region_filter", "Region", choices, multiple=True
            ),
        )

    # FILTERED DATA

    @reactive.calc
    def df_demand_sector_group_filtered():
        d = df_energy_demand
        if inputs.demand_sector_group_filter():
            d = d[
                d["SectorGroup"].astype(str).isin(inputs.demand_sector_group_filter())
            ]
        return d

    @reactive.calc
    def df_demand_enduse_group_filtered():
        d = df_energy_demand
        if inputs.demand_enduse_group_filter():
            d = d[
                d["EnduseGroup"].astype(str).isin(inputs.demand_enduse_group_filter())
            ]
        return d

    @reactive.calc
    def df_demand_tech_group_filtered():
        d = df_energy_demand
        if inputs.demand_tech_group_filter():
            d = d[
                d["TechnologyGroup"].astype(str).isin(inputs.demand_tech_group_filter())
            ]
        return d

    @reactive.calc
    def df_demand_filtered():
        d = df_energy_demand

        if inputs.demand_sector_group_filter():
            d = d[
                d["SectorGroup"].astype(str).isin(inputs.demand_sector_group_filter())
            ]
        if inputs.demand_sector_filter():
            d = d[d["Sector"].astype(str).isin(inputs.demand_sector_filter())]
        if inputs.demand_tech_group_filter():
            d = d[
                d["TechnologyGroup"].astype(str).isin(inputs.demand_tech_group_filter())
            ]
        if inputs.demand_tech_filter():
            d = d[d["Technology"].astype(str).isin(inputs.demand_tech_filter())]
        if inputs.demand_enduse_group_filter():
            d = d[
                d["EnduseGroup"].astype(str).isin(inputs.demand_enduse_group_filter())
            ]
        if inputs.demand_enduse_filter():
            d = d[d["EndUse"].astype(str).isin(inputs.demand_enduse_filter())]
        if inputs.demand_fuel_filter():
            d = d[d["Fuel"].astype(str).isin(inputs.demand_fuel_filter())]
        if inputs.demand_region_filter():
            d = d[d["Region"].astype(str).isin(inputs.demand_region_filter())]

        return d

    @outputs
    @render.ui
    def demand_filters():
        return ui.layout_columns(
            ui.div(
                ui.output_ui("demand_sector_group_filters"),
                ui.output_ui("demand_sector_filters"),
            ),
            ui.div(
                ui.output_ui("demand_tech_group_filters"),
                ui.output_ui("demand_tech_filters"),
            ),
            ui.div(
                ui.output_ui("demand_enduse_group_filters"),
                ui.output_ui("demand_enduse_filters"),
            ),
            ui.output_ui("demand_region_filters"),
            ui.output_ui("demand_fuel_filters"),
        )

    # GROUPING
    @reactive.calc
    def df_demand_grouped():
        d = df_demand_filtered()
        # d = df_energy_demand
        return (
            d.groupby(base_cols + [inputs.demand_group()])["Value"].sum().reset_index()
        )

    @outputs(id="demand_chart")
    @render_altair
    def _():
        d = df_demand_grouped()
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
            + [inputs.demand_group()],
        )

        return (
            alt.Chart(dc)
            .mark_bar(size=50, opacity=0.85)
            .encode(
                x=alt.X("Period:N", title="Year"),
                y=alt.Y("Value:Q", title="PJ"),
                color=f"{inputs.demand_group()}:N",
                tooltip=[
                    # alt.Tooltip("PlantName:N", title=""),
                    alt.Tooltip(
                        f"{inputs.demand_group()}:N", title=inputs.demand_group()
                    ),
                    alt.Tooltip("Value:Q", title="PJ", format=",.2f"),
                    # alt.Tooltip("y:Q", title="Y", format=",.2f"),
                ],
            )
        )

    @outputs
    @render.download(filename="energy_demand_data.csv")
    def download_demand_data():
        # yield file chunks to the client
        with open(FINAL_DATA / "energy_demand.csv", "rb") as f:
            yield from f


demand_ui = ui.page_fluid(
    ui.row(
        ui.column(6, ui.output_ui("energy_demand_title")),
        ui.column(
            4, ui.input_select("demand_group", "Group by:", demand_group_options)
        ),
        ui.column(2, ui.download_button("download_demand_data", "Download raw data")),
    ),
    ui.span("Filters"),
    ui.output_ui("demand_filters"),
    output_widget("demand_chart"),
)
