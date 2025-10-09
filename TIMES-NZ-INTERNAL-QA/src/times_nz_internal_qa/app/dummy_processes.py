"""
App processing for dummy processes
"""

import altair as alt
import pandas as pd
from shiny import reactive, ui
from shinywidgets import output_widget, render_altair
from times_nz_internal_qa.utilities.data_formatting import (
    complete_periods,
)
from times_nz_internal_qa.utilities.filepaths import FINAL_DATA

dummy_energy = pd.read_csv(FINAL_DATA / "dummy_energy.csv")
dummy_demand = pd.read_csv(FINAL_DATA / "dummy_demand.csv")


dummy_energy_group_cols = ["Scenario", "Attribute", "Variable", "Period"]
dummy_energy_group_options = ["Fuel", "Commodity", "Region"]
dummy_demand_group_cols = ["Scenario", "Attribute", "Variable", "Period"]

dummy_demand_group_options = [
    "SectorGroup",
    "Sector",
    "EndUse",
    "Commodity",
    "Region",
]


# pylint:disable = unused-argument
def dummy_server(inputs, outputs, session):
    """
    Server functions for dummy process module
    """

    @reactive.calc
    def dummy_energy_filtered():
        d = dummy_energy

        if inputs.dummy_demand_sector_group_filter():
            d = d[
                d["SectorGroup"].astype(str).isin(inputs.demand_sector_group_filter())
            ]

        return d

    @reactive.calc
    def dummy_demand_grouped():
        return (
            dummy_demand.groupby(
                dummy_demand_group_cols + [inputs.dummy_demand_group()]
            )["Value"]
            .sum()
            .reset_index()
        )

    @reactive.calc
    def dummy_energy_grouped():
        return (
            dummy_energy.groupby(
                dummy_energy_group_cols + [inputs.dummy_energy_group()]
            )["Value"]
            .sum()
            .reset_index()
        )

    @outputs(id="dummy_demand_chart")
    @render_altair
    def _():
        d = dummy_demand_grouped()
        dc = complete_periods(
            d,
            period_list=range(2023, 2051),
            # base cols but not period
            category_cols=[
                "Scenario",
                "Attribute",
                "Variable",
            ],
        )

        return (
            alt.Chart(dc)
            .mark_bar(size=50, opacity=0.85)
            .encode(
                x=alt.X("Period:N", title="Year"),
                y=alt.Y("Value:Q", title="PJ"),
                color=f"{inputs.dummy_demand_group()}:N",
                tooltip=[
                    # alt.Tooltip("PlantName:N", title=""),
                    alt.Tooltip(
                        f"{inputs.dummy_demand_group()}:N",
                        title=inputs.dummy_demand_group(),
                    ),
                    alt.Tooltip("Value:Q", title="PJ", format=",.2f"),
                    # alt.Tooltip("y:Q", title="Y", format=",.2f"),
                ],
            )
        )

    @outputs(id="dummy_energy_chart")
    @render_altair
    def _():
        d = dummy_energy_grouped()
        dc = complete_periods(
            d,
            period_list=range(2023, 2051),
            # base cols but not period
            category_cols=[
                "Scenario",
                "Attribute",
                "Variable",
            ],
        )

        return (
            alt.Chart(dc)
            .mark_bar(size=50, opacity=0.85)
            .encode(
                x=alt.X("Period:N", title="Year"),
                y=alt.Y("Value:Q", title="PJ"),
                color=f"{inputs.dummy_energy_group()}:N",
                tooltip=[
                    # alt.Tooltip("PlantName:N", title=""),
                    alt.Tooltip(
                        f"{inputs.dummy_energy_group()}:N",
                        title=f"{inputs.dummy_energy_group()}",
                    ),
                    alt.Tooltip("Value:Q", title="PJ", format=",.2f"),
                    # alt.Tooltip("y:Q", title="Y", format=",.2f"),
                ],
            )
        )


dummy_ui = ui.page_fluid(
    ui.row(ui.em("If the model is calibrated correctly, this page will be blank")),
    ui.em(":("),
    ui.row(
        # ui.column(6,ui.output_ui("energy_demand_title")),
        # ui.column(4,ui.input_select("demand_group", "Group by:", demand_group_options)),
        # ui.column(2,ui.download_button("download_demand_data", "Download raw data")),
    ),
    ui.div(
        ui.h2("dummy demand"),
        ui.input_select("dummy_demand_group", "Group by:", dummy_demand_group_options),
        style="display:flex; align-items:center; justify-content:space-between;",
    ),
    output_widget("dummy_demand_chart"),
    ui.div(
        ui.h2("dummy energy"),
        ui.input_select("dummy_energy_group", "Group by:", dummy_energy_group_options),
        style="display:flex; align-items:center; justify-content:space-between;",
    ),
    output_widget("dummy_energy_chart"),
)
