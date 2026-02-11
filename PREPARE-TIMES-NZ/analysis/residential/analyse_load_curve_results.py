"""
Builds a charts of the residential load curves from model results

Uses post-processed times results for a given scenario!

Not part of workflow, just some testing
"""

# libraries
import pandas as pd

# pylint: disable = unused-import, unused-wildcard-import, wildcard-import
from plotnine import *
from prepare_times_nz.stage_0.stage_0_settings import BASE_YEAR
from prepare_times_nz.utilities.filepaths import ANALYSIS, TIMES_LOCATION

RESULTS_LOCATION = TIMES_LOCATION / "TIMES-NZ-INTERNAL-QA" / "data" / "clean_results"


# constants

SCENARIO = "traditional-v3_0_2-rippleadjust"
OUTPUT_LOCATION = ANALYSIS / "results/load_curves"


eeca_colours = {
    "emerald": "#41B496",
    "teal": "#447474",
    "navy": "#164057",
    "coral": "#ED6D63",
    "forest": "#3C4C49",
}

chart_cols = [
    eeca_colours["navy"],
    eeca_colours["teal"],
    eeca_colours["coral"],
    eeca_colours["emerald"],
]


def split_timeslices(df, make_nice_labels=True):
    """
    Takes an input df with TimeSlice and creates new variables:
    TimeOfDay
    DayType
    Season

    leaves TimeSlice intact

    By default, makes these nicer to read
    """

    df = df.copy()

    df["TimeOfDay"] = df["TimeSlice"].str.rsplit("-", n=1).str[1]
    df["DayType"] = (
        df["TimeSlice"].str.rsplit("-", n=1).str[0].str.rsplit("-", n=1).str[1]
    )
    df["Season"] = df["TimeSlice"].str.rsplit("-", n=2).str[0]

    if make_nice_labels:

        df["DayType"] = df["DayType"].map({"WE": "Weekend", "WK": "Weekday"})

        df["TimeOfDay"] = df["TimeOfDay"].map({"D": "Day", "N": "Night", "P": "Peak"})

        df["Season"] = df["Season"].map(
            {"SUM": "Summer", "WIN": "Winter", "FAL": "Autumn", "SPR": "Spring"}
        )

    return df


def get_res_baseyear_load(scenario=SCENARIO):
    """
    Loads the scenario results for res baseyear demand
    """
    df = pd.read_parquet(RESULTS_LOCATION / "electricity_demand_by_timeslice.parquet")

    df = df[df["Scenario"] == scenario]
    df = df[df["SectorGroup"] == "Residential"]
    df = df[df["Period"] == str(BASE_YEAR)]

    # better mapping of uses

    use_map = {
        "Low Temperature Heat (<100 C), Clothes Drying": "Other",
        "Intermediate Heat (100-300 C), Cooking": "Cooking",
        "Low Temperature Heat (<100 C), Clothes Washing": "Other",
        "Low Temperature Heat (< 100 C), Dishwashers": "Other",
        "Refrigeration": "Other",
        "Low Temperature Heat (<100 C), Space Heating": "Space heating",
        "Space Cooling": "Other",
        "Low Temperature Heat (<100 C), Water Heating": "Water heating",
        "Electronics and Other Electrical Uses": "Other",
        "Lighting": "Other",
    }

    df["EndUseChart"] = df["EndUse"].map(use_map)

    df = split_timeslices(df)

    return df


def make_chart(df):
    """
    Generates chart from data, filtering weekday first
    """
    chart_df = df[df["DayType"] == "Weekday"]

    # totals = chart_df.groupby(["Season", "DayType", "TimeOfDay"])["GW"].sum().reset_index()
    # print(totals)

    chart = (
        ggplot(chart_df, aes(y="GW", x="TimeOfDay", fill="EndUseChart"))
        + geom_col()
        + facet_wrap("~Season")
        + scale_fill_manual(values=chart_cols)
        + labs(x="TimeOfDay", y="GW", fill="Use Type", title="")
        + theme_minimal()
        + theme(title=element_blank())
    )

    chart.save(OUTPUT_LOCATION / "res_rbs_weekday_ripple.png")


def main():
    """entrypoint"""

    df = get_res_baseyear_load()
    make_chart(df)


if __name__ == "__main__":
    main()
