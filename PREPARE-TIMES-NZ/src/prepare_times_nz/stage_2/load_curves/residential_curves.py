"""
Uses RBS data on electricity demand time of use
Converts to TIMES timeslices and end use categories to create
specific commodity fractions per end use
"""

import pandas as pd
from prepare_times_nz.stage_0.stage_0_settings import BASE_YEAR
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.filepaths import (
    CONCORDANCES,
    DATA_RAW,
    STAGE_1_DATA,
    STAGE_2_DATA,
)

# ASSUMPTIONS -----------------------------------------------

RIPPLE_SHARE = 0.5

# the share of space conditioning dedicated to heating each season
HEATING_SHARE_ASSUMPTIONS = {
    "Winter": 1,
    "Summer": 0,
    "Spring": 0.9,
    "Autumn": 0.9,
}

# Filepaths ----------------------------------------

LOAD_CURVE_DATA = STAGE_2_DATA / "settings/load_curves"
OUTPUT_LOCATION = STAGE_2_DATA / "settings/load_curves"

# CONCORDANCE FILES ----------------------------------------
# end use codes
RBS_END_USE_FILE = CONCORDANCES / "residential/rbs_end_use_codes.csv"
USE_CODES_FILE = CONCORDANCES / "residential/use_codes.csv"

# times of day
TIME_OF_DAY_FILE = DATA_RAW / "user_config/settings/time_of_day_types.csv"

# FUNCTIONS ------------------------------------------------------------------


def add_rbs_use_concordance(df, rbs_conc=RBS_END_USE_FILE, use_codes=USE_CODES_FILE):
    """
    Load custom concordance file to map rbs uses to times use categories
    """

    df_conc = pd.read_csv(rbs_conc)
    df_use_codes = pd.read_csv(use_codes)

    # merge, deleting missing categories (transport + generation currently )
    df = df.merge(df_conc, on="EndUseCategory", how="inner")
    # NOTE cartesian join (multiple times categories per some rbs categories )
    # so be cautious with adding the results
    # add the use codes
    df = df.merge(df_use_codes, on="EndUse", how="left")

    return df


def split_space_conditioning(df):
    """
    We want to split space conditioning into heating/cooling
    We do this based on assumptions per season

    Assumes a df input of the raw RBS data
    NOTE that this step will be required for our mapping to work

    Includes seasonal assumptions that we can probably tweak

    Should make some charts about it

    """

    # set assumptions

    # split out space conditioning
    df_cond = df[df["EndUseCategory"] == "Space conditioning"].copy()
    # remove from main
    df_no_cond = df[df["EndUseCategory"] != "Space conditioning"].copy()
    df_cond["HeatShare"] = df_cond["Season"].map(HEATING_SHARE_ASSUMPTIONS)

    # calc heating
    df_heating = df_cond.copy()
    df_heating["EndUseCategory"] = "Space heating"
    df_heating["Power"] = df_heating["Power"] * df_heating["HeatShare"]

    # calc cooling
    df_cooling = df_cond.copy()
    df_cooling["EndUseCategory"] = "Space cooling"
    df_cooling["Power"] = df_cooling["Power"] * (1 - df_cooling["HeatShare"])

    # combine and return
    out = pd.concat([df_heating, df_cooling, df_no_cond])
    out = out.drop("HeatShare", axis=1)

    return out


def convert_hour_to_timeofday(df: pd.DataFrame) -> pd.DataFrame:
    """
    This function takes a dataframe with an hour variable
    and creates the Time_Of_Day variable.

    This uses an input assumptions file with
    "Hour" and "Time_Of_Day" variables

    We set default to night (this mostly just covers DST hours)

    """
    time_of_day_types = pd.read_csv(TIME_OF_DAY_FILE)
    # # we create a dict and map these rather than merging
    # its faster - saves ~4 seconds per run
    hour_to_time = dict(
        zip(time_of_day_types["Hour"], time_of_day_types["Time_Of_Day"])
    )
    df["Time_Of_Day"] = df["Hour"].map(hour_to_time)
    df["Time_Of_Day"] = df["Time_Of_Day"].fillna("N")

    return df


def make_rbs_timeslices(df):
    """
    Based on the RBS data, creates TIMES-NZ timeslice categories

    expects input df with variables:

    Season(str): (Autumn, Spring, Winter, Summer)
    DayType(str): (WD, WE)
    Hour(int): (0-23)

    We use custom handling for season and daytype here
    and import an hour map used elsewhere
        for definition consistency

    """

    df = df.copy()

    # using a hardcoded map here
    season_map = {
        "Autumn": "FAL-",
        "Winter": "WIN-",
        "Spring": "SPR-",
        "Summer": "SUM-",
    }
    df["Season"] = df["Season"].map(season_map)

    # remapping the daytype labels
    daytype_map = {"WD": "WK-", "WE": "WE-"}

    df["DayType"] = df["DayType"].map(daytype_map)

    # timeofday definitions. needs ["Hour"] in df

    df = convert_hour_to_timeofday(df)

    # combine

    df["TimeSlice"] = df["Season"] + df["DayType"] + df["Time_Of_Day"]

    return df


def aggregate_rbs_loadcurves(df, start_year=2000, latest_year=BASE_YEAR):
    """
    assuming the input df has the necessary categories, we filter and aggregate
    to get our total output
    Note the original unit definition is MW,
    which is equivalent to MWh on a per hour basis

    """

    df = df.copy()

    if start_year > latest_year:
        raise ValueError("Start year must be less than or equal to the latest year")

    # get specific range
    # by default we are taking full historical curve up to base year
    df = df[df["Year"] <= latest_year]
    df = df[df["Year"] >= start_year]

    # aggregate out random doublecounts. this ensures our grain is correct
    # which we need for counts later
    full_group_vars = [
        "Year",
        "Region",
        "Season",
        "TimeSlice",
        "Hour",
        "EndUse",
        "EndUse_TIMES",
    ]
    # need to control for hours in slice based on time of day lookup
    # RBS data is average load per hour, we want average load per slice
    # so not necessary to do other dividing unless we also take average across several years
    # need to add hour counts and year counts
    # actual aggregation including hour counts
    # filter year fort now can expand method later
    # aggregate to ts per year
    df = df.groupby(full_group_vars)["Power"].sum().reset_index()
    df = df.groupby(
        ["Year", "TimeSlice", "EndUse", "EndUse_TIMES", "Season"], as_index=False
    ).agg(Power=("Power", "sum"), Hours=("Power", "count"))
    df["AverageMW"] = df["Power"] / df["Hours"]

    # sort, not necessary, just tidy
    df = df.sort_values(["EndUse", "EndUse_TIMES", "Year", "Season"])
    return df


def agg_years(df):
    """
    Assumes data is aggregated by slice, but not year.
    Aggregates per year, so effectively taking an average over the provided years
    """
    # average out each year in the range
    year_count = len(df["Year"].unique())
    print(f"includes data from {year_count} years")

    df = df.groupby(
        ["TimeSlice", "EndUse", "EndUse_TIMES", "Season"], as_index=False
    ).agg(AverageMW=("AverageMW", "sum"))

    df["AverageMW"] = df["AverageMW"] / year_count

    return df


def shift_ripple_water_heating(df, ripple_share=RIPPLE_SHARE):
    """
    Adjust ripple-controlled water heating to nighttime in each day period
    Doing this based on the calculated GWh and an input share

    Can slot this in before creating the com_fr from gwh

    """

    if not 0 <= ripple_share <= 1:
        raise ValueError("ripple_share must be between 0 and 1.")

    out = df.copy()
    # get ts components
    ts_prefix = out["TimeSlice"].str.rsplit("-", n=1).str[0]
    ts_tod = out["TimeSlice"].str.rsplit("-", n=1).str[1]

    # hotwater mapping
    is_hw = out["EndUse"].eq("Low Temperature Heat (<100 C), Water Heating")
    # id timeslices
    hw_peak = is_hw & ts_tod.eq("P")
    hw_night = is_hw & ts_tod.eq("N")

    # amount to adjust
    delta = out.loc[hw_peak, "GWh"] * ripple_share
    # remove from hw peak
    out.loc[hw_peak, "GWh"] = out.loc[hw_peak, "GWh"] - delta

    # gather how much was added for each timeslice prefix group
    add_by_prefix = (
        pd.DataFrame({"_prefix": ts_prefix[hw_peak].values, "_add": delta.values})
        .groupby("_prefix", as_index=False)["_add"]
        .sum()
    )

    # add to the main df
    out["_prefix"] = ts_prefix.values
    out = out.merge(add_by_prefix, on="_prefix", how="left")
    out["_add"] = out["_add"].fillna(0.0)
    # use to add the delta to the night timeslice
    out.loc[hw_night, "GWh"] = out.loc[hw_night, "GWh"] + out.loc[hw_night, "_add"]
    # trim excess
    out = out.drop(columns=["_prefix", "_add"])

    return out


def make_com_fr(df, adjust_hw_for_ripple=False, ripple_share=RIPPLE_SHARE):
    """
    Convert inputs to commodity fraction

    ie the share of demand for each use in each slice
    Only these proportions should actually be used

    If we take the GWh we'll double count
         unless we split up white goods and any other larger rbs categories


    Adds optional method to shift a % of peak water heating demand to Night
    """

    df = df.copy()
    df = agg_years(df)

    yrfr = pd.read_csv(LOAD_CURVE_DATA / "yrfr.csv")

    # estimate gwh per each cat
    # (NOTE that this will be incorrcet for RBS categories with multiple TIMES use codes
    # due to cartesian join
    # we only want shares, and some will have matching shares

    df = df.merge(yrfr, on="TimeSlice", how="left")

    df["MWh"] = df["AverageMW"] * df["YRFR"] * 365 * 24
    df["GWh"] = df["MWh"] / 1e3

    if adjust_hw_for_ripple:

        df = shift_ripple_water_heating(df, ripple_share)

    df["LoadCurve"] = df["GWh"] / df.groupby(["EndUse"])["GWh"].transform("sum")

    df = df.rename(columns={"EndUse_TIMES": "Commodity"})

    # we also expand these for joined/detached, forming the same base commoditygroups
    df = pd.concat(
        [
            df.assign(Commodity="JD-" + df["Commodity"]),
            df.assign(Commodity="DD-" + df["Commodity"]),
        ],
        ignore_index=True,
    )

    return df


def main():
    """
    Entrypoint. Coordinates necessary functions
    """

    # load data
    rbs_raw = pd.read_parquet(
        STAGE_1_DATA / "res_baseline" / "power_demand_by_tou.parquet"
    )

    # split space conditioning
    rbs_df = split_space_conditioning(rbs_raw)
    # add the end uses. not this deletes unmatched categories
    rbs_df = add_rbs_use_concordance(rbs_df)
    # convert rbs data to our slices
    rbs_df = make_rbs_timeslices(rbs_df)
    # aggregate data across our slices
    rbs_df = aggregate_rbs_loadcurves(rbs_df)
    # convert to com_fr outputs
    com_fr = make_com_fr(rbs_df)
    # save
    _save_data(
        com_fr, "residential_curves.csv", "Residential load curves", OUTPUT_LOCATION
    )
    # repeat with ripple adjustment for alternative approach
    com_fr_adjust = make_com_fr(rbs_df, adjust_hw_for_ripple=True)
    _save_data(
        com_fr_adjust,
        "residential_curves_with_ripple.csv",
        "Residential load curves (rippled)",
        OUTPUT_LOCATION,
    )


if __name__ == "__main__":
    main()

    #
    # main2()
