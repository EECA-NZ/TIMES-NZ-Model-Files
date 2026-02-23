"""
Generates charts of the results of the stage 3 data for scenario gas projectiosn
"""

# pylint: disable = unused-import, unused-wildcard-import, wildcard-import
import numpy as np
import pandas as pd
from plotnine import *
from prepare_times_nz.utilities.filepaths import ANALYSIS, STAGE_3_DATA

# Directories -------------------------------------------------------


# output


OUTPUT_LOCATION = ANALYSIS / "results/oil_and_gas_projections"
OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)

# input data
OG_DATA = STAGE_3_DATA / "oil_and_gas"
INPUT_DATA = OG_DATA / "oil_and_gas_projections.csv"


# separate analysis functions -----------------


def aggregate_df(df, n):
    """aggregate all fields outside of the top n into "Other"
    The "Other" category is also forced to the end by converting the field to categorical
    Which is useful for plotting when it should always go last
    """

    df_top = df.groupby("Field")["Value"].sum().reset_index()
    df_top = df_top.sort_values("Value", ascending=False)
    # get top n fields
    top_n = df_top.nlargest(n, "Value")

    df["Field"] = np.where(
        df["Field"].isin(top_n["Field"]), df["Field"], "Other fields"
    )

    df_agg = (
        df.groupby(["Field", "Year", "Unit", "Variable", "ResourceType"])["Value"]
        .sum()
        .reset_index()
    )

    df_agg["ResourceType"] = np.where(
        df_agg["ResourceType"] == "2C", "Contingent", "Existing"
    )

    # force order through categoricals

    order = [c for c in df_agg["Field"].unique() if c != "Other fields"]
    order.append("Other fields")  # force it last

    df_agg["Field"] = pd.Categorical(df_agg["Field"], categories=order, ordered=True)

    return df_agg


def print_national_chart(df):
    """takes aggregated data and saves a national chart of output projections"""

    # colours
    eeca_teal = "#447474"
    eeca_coral = "#ED6D63"
    colours = [eeca_coral, eeca_teal]

    df = df.groupby(["Year", "ResourceType"])["Value"].sum().reset_index()

    chart = (
        ggplot(df, aes(y="Value", x="Year"))
        + geom_area(aes(fill="ResourceType"))
        + scale_fill_manual(values=colours)
        + labs(
            x="Year",
            y="PJ",
            colour="Scenario",
            # title="Gas production projections",
            fill="Resource",
            subtitle="Including 60% contingent",
        )
        + theme_minimal()
        # + theme(panel_grid_major=element_blank())
    )
    chart_name = "gas_projections_national.png"
    chart.save(OUTPUT_LOCATION / chart_name, dpi=300, height=5, width=8)


def print_field_chart(df):
    """takes aggregated data and saves a per-field chart of output projections"""

    # colours
    eeca_teal = "#447474"
    eeca_coral = "#ED6D63"
    colours = [eeca_coral, eeca_teal]

    chart = (
        ggplot(df, aes(y="Value", x="Year"))
        + geom_area(aes(fill="ResourceType"))
        + facet_wrap("~Field")
        # + coord_flip()
        + scale_fill_manual(values=colours)
        + labs(
            x="Year",
            y="PJ",
            colour="Scenario",
            # title="Gas production projections",
            fill="Resource",
            subtitle="Including 60% contingent",
        )
        + theme_minimal()
        # + theme(panel_grid_major=element_blank())
    )
    chart_name = "gas_projections_by_field.png"
    chart.save(OUTPUT_LOCATION / chart_name, dpi=300, height=5, width=8)


def main():
    """entrypoint"""

    df = pd.read_csv(INPUT_DATA)
    agg = aggregate_df(df, 8)

    print_national_chart(agg)
    print_field_chart(agg)


if __name__ == "__main__":
    main()
