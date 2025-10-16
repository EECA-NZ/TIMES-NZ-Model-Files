"""
Takes the input/output demand projections and generates some charts
"""

import pandas as pd

# pylint: disable = wildcard-import, unused-wildcard-import
from plotnine import *
from prepare_times_nz.utilities.filepaths import ANALYSIS, STAGE_3_DATA

ANALYSIS_OUTPUT = ANALYSIS / "results/demand_projections"
PROJECTIONS_DATA = STAGE_3_DATA / "demand_projections"


def make_chart(df, filename):
    """Build a chart showing the industrial demand projections per sector"""

    # colours
    # should one day extract these to a proper module to import
    eeca_teal = "#447474"
    eeca_coral = "#ED6D63"
    colours = [eeca_coral, eeca_teal]

    # ignore these (handled differently in model)
    sectors_to_remove = ["Urea", "Methanol"]
    df = df[~df["Sector"].isin(sectors_to_remove)]

    # aggregate
    df = df.groupby(["Sector", "Year", "Scenario"])["Value"].sum().reset_index()

    # plot
    chart = (
        ggplot(df, aes(y="Value", x="Year"))
        + geom_line(aes(colour="Scenario"), size=1)
        + scale_colour_manual(values=colours, na_value="grey")
        + facet_wrap("Sector", ncol=3)
        + labs(
            x="Year",
            y="PJ",
            colour="Scenario",
            title="Industrial sector demand projections",
        )
        + theme_minimal()
        + theme(legend_position="bottom")
    )

    ANALYSIS_OUTPUT.mkdir(parents=True, exist_ok=True)
    chart.save(ANALYSIS_OUTPUT / filename, dpi=300, height=6, width=8)


def main():
    """entrypoint"""
    # output (final energy  demand )
    input_df = pd.read_csv(PROJECTIONS_DATA / "industrial_input.csv")
    make_chart(input_df, "industry_projections_input_energy.png")

    output_df = pd.read_csv(PROJECTIONS_DATA / "industrial_output.csv")
    make_chart(output_df, "industry_projections_output_energy.png")


if __name__ == "__main__":
    main()
