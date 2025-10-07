"""
server functions for app.py
"""

import altair as alt
from shiny import reactive
from shinywidgets import render_altair
from times_nz_internal_qa.app.formatting import get_ele_gen_df

ele_gen_df, unit_map = get_ele_gen_df()


# maybe
alt.data_transformers.disable_max_rows()

# define base columns that we must always group by
base_cols = [
    "Scenario",
    "Attribute",
    "Variable",
    "Period",
    "Unit",
]


# must include session in server declaration even if unused.
# Also redefining builtin 'input' hmm
# pylint:disable = unused-argument, redefined-builtin
def server(inputs, outputs, session):
    """
    The app server
    """

    @reactive.calc
    def dfi():
        df = ele_gen_df.copy()

        df = df[df["Variable"] == inputs.variable()]
        df = df.groupby(base_cols + [inputs.group()])["Value"].sum().reset_index()
        return df

    @outputs(id="chart")
    @render_altair
    def _():
        d = dfi()
        var = inputs.variable()
        unit = unit_map.get(var, "")
        return (
            alt.Chart(d)
            .mark_bar(size=80, opacity=0.85)
            .encode(
                x=alt.X("Period:O", title="Year"),
                y=alt.Y("Value:Q", title=f"{unit}"),
                color=f"{inputs.group()}:N",
                tooltip=[
                    # alt.Tooltip("PlantName:N", title=""),
                    alt.Tooltip("TechnologyGroup:N", title="Tech"),
                    alt.Tooltip("Value:Q", title=f"{unit}", format=",.2f"),
                    # alt.Tooltip("y:Q", title="Y", format=",.2f"),
                ],
            )
        )
