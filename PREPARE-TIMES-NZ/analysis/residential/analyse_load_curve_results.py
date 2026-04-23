"""
Builds a charts of the residential load curves from model results

Uses post-processed times results for a given scenario!

Not part of workflow, just some testing


psudo code:

1) get residential baseyear demand from eeud data
2) get load curve parameters
"""

# libraries
import pandas as pd

# pylint: disable = unused-import, unused-wildcard-import, wildcard-import
from plotnine import *
from prepare_times_nz.stage_0.stage_0_settings import BASE_YEAR
from prepare_times_nz.utilities.filepaths import (
    ANALYSIS,
    STAGE_1_DATA,
    STAGE_2_DATA,
    TIMES_LOCATION,
)

RESULTS_LOCATION = TIMES_LOCATION / "TIMES-NZ-INTERNAL-QA" / "data" / "clean_results"


# Get data

EEUD_FILE = STAGE_1_DATA / "eeud/eeud.csv"
LOAD_CURVE_DATA = STAGE_2_DATA / "settings/load_curves/"

RES_DEMAND_FILE = STAGE_2_DATA / "residential/baseyear_residential_demand.csv"

YRFR_FILE = STAGE_2_DATA / "settings/load_curves/yrfr.csv"


PJ_TO_GWH = 1000 / 3.6

# constants

SCENARIO = "steady-v3_0_2-rippleadjust"
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

SEASON_ORDER = ["SUM", "FAL", "WIN", "SPR"]
DAY_TYPE_ORDER = ["WK", "WE"]
TIME_OF_DAY_ORDER = ["D", "P", "N"]

SEASON_LABELS = {
    "SUM": "Summer",
    "WIN": "Winter",
    "FAL": "Autumn",
    "SPR": "Spring",
}
DAY_TYPE_LABELS = {"WE": "Weekend", "WK": "Weekday"}
DAY_TYPE_AXIS_LABELS = {"WE": "Wknd.", "WK": "Week"}
TIME_OF_DAY_LABELS = {"D": "Day", "N": "Night", "P": "Peak"}

TIMESLICE_ORDER = [
    f"{season}-{day_type}-{time_of_day}"
    for season in SEASON_ORDER
    for day_type in DAY_TYPE_ORDER
    for time_of_day in TIME_OF_DAY_ORDER
]


def get_res_demand():
    """Returns total residential electricity demand for baseyear"""

    df = pd.read_csv(RES_DEMAND_FILE)

    df = df[df["Variable"] == "InputEnergy"]
    df = df[df["Fuel"] == "Electricity"]

    # should be already filtered to baseyear but we just make sure

    df = df[df["Year"] == BASE_YEAR]

    # input value per demand commodity

    df = df.groupby("CommodityOut")["Value"].sum().reset_index()

    df = df.rename(columns={"CommodityOut": "Commodity", "Value": "PJ"})

    return df


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

    parts = df["TimeSlice"].astype(str).str.split("-", expand=True)
    df["SeasonCode"] = parts[0]
    df["DayTypeCode"] = parts[1]
    df["TimeOfDayCode"] = parts[2]
    df["TimeOfDay"] = df["TimeOfDayCode"]
    df["DayType"] = df["DayTypeCode"]
    df["Season"] = df["SeasonCode"]

    if make_nice_labels:
        df["DayType"] = df["DayType"].map(DAY_TYPE_LABELS)
        df["TimeOfDay"] = df["TimeOfDay"].map(TIME_OF_DAY_LABELS)
        df["Season"] = df["Season"].map(SEASON_LABELS)

    df["TimeSliceLabel"] = (
        df["SeasonCode"].map(SEASON_LABELS)
        + "\n"
        + df["DayTypeCode"].map(DAY_TYPE_AXIS_LABELS)
        + " "
        + df["TimeOfDayCode"].map(TIME_OF_DAY_LABELS)
    )
    df["TimeSlice"] = pd.Categorical(
        df["TimeSlice"], categories=TIMESLICE_ORDER, ordered=True
    )

    return df


def get_load_curves(filename="residential_curves_ripple_50.csv"):
    """
    Pull in load curve data
    """

    df = pd.read_csv(LOAD_CURVE_DATA / filename)

    # validate! each Commodity should add to 1
    # test = df.groupby("Commodity")["LoadCurve"].sum().reset_index()
    # print(test)

    # before aggregating, we convert to GWh based on our demand

    # only need these to join on
    df = df[["TimeSlice", "Commodity", "EndUse", "LoadCurve"]]

    # add the demand

    res_demand = get_res_demand()

    df = df.merge(res_demand, how="left", on="Commodity")

    # split demand by commodity and timeslice
    df["PJ"] = df["PJ"] * df["LoadCurve"]

    # aggregate by use group
    # broad end use mapping

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

    df["EndUse"] = df["EndUse"].map(use_map)

    # aggregate demand by slice and broad grouyp
    df = df.groupby(["TimeSlice", "EndUse"])["PJ"].sum().reset_index()

    # make nicer timeslices
    df = split_timeslices(df)

    return df


def convert_pj_to_average_load(df):
    """
    Docstring for convert_pj_to_average_load

    expects an input df with "PJ" and "TimeSlice" variables

    uses year fraction data to define the timeslice length
    converts the PJ to GWh

    uses GWh and TimeSlice length to infer average GW load per slice

    Can do this on any aggregation assuming PJ aggregation
    """

    # load year fractions

    yrfr_data = pd.read_csv(YRFR_FILE)
    # create hours per slice

    df = df.merge(yrfr_data, on="TimeSlice", how="left")

    df["Hours"] = 8760 * df["YRFR"]

    # create average GW
    df["GWh"] = df["PJ"] * PJ_TO_GWH
    df["GW"] = df["GWh"] / df["Hours"]

    return df


def make_chart(df):
    """
    Generates chart from data, filtering weekday first
    """
    chart_df = df[df["DayType"] == "Weekday"]

    print(chart_df)

    totals = (
        chart_df.groupby(["Season", "DayType", "TimeOfDay"])["GW"].sum().reset_index()
    )
    # print(totals)

    chart = (
        ggplot(chart_df, aes(y="GW", x="TimeOfDay", fill="EndUse"))
        + geom_col()
        + facet_wrap("~Season")
        + scale_fill_manual(values=chart_cols)
        + labs(y="GW", x="Time of day", fill="Use type")
        + theme_minimal()
        + theme(plot_title=element_blank())
        + geom_text(
            totals,
            aes(x="TimeOfDay", y="GW", label="round(GW, 1)"),
            inherit_aes=False,
            va="bottom",
            size=11,
        )
        + scale_y_continuous(expand=(0, 0.5))
    )

    chart.save(OUTPUT_LOCATION / "res_rbs_weekday_ripple.png")
    chart.save(OUTPUT_LOCATION / "res_rbs_weekday_ripple.pdf")


def main():
    """entrypoint"""

    # df = get_res_baseyear_load()
    # make_chart(df)

    curves = get_load_curves()

    load_df = convert_pj_to_average_load(curves)

    make_chart(load_df)


if __name__ == "__main__":
    main()
