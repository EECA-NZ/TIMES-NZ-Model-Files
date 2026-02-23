"""
Loads population projection data
 and create indices based on the BASE YEAR


1 get pop
2 index to base year
3 create "population index" which is just 1 for base year
 then carries forward by population growth

Currently only using one projection at national level
For both scenarios

Would be sensible to split this by island - would be very easy to implement

"""

import pandas as pd
from prepare_times_nz.stage_0.stage_0_settings import BASE_YEAR
from prepare_times_nz.utilities.filepaths import STAGE_1_DATA

# constants
SCENARIO = "50th percentile (median)"

PROJECTIONS = STAGE_1_DATA / "statsnz/projections_national_2024.csv"
HISTORICAL = STAGE_1_DATA / "statsnz/estimated_resident_population.csv"


# function
def get_national_population_growth_index(
    scenario,
    base_year=BASE_YEAR,
    projections_file=PROJECTIONS,
    historical_file=HISTORICAL,
):
    """
    Uses Stats NZ historical and projected national population data
    Creates an output dataframe of indexed values
    (where base year = 1, and future years scale from there)
    This can be used to scale up demands for population-driven commodities
    Simple, national-level approach

    Note: if the historical data goes past the base year, we keep the historical data.
    If there is overlap between projections and historical,
         we take only the historical data

    Only returns the df - does not save it to staging area
    This means dependencies (past stage 1) don't matter. just import this function.

    """

    # get historical data

    df_h = pd.read_csv(historical_file)
    df_h = df_h[df_h["Year"] >= base_year]
    df_h = df_h[df_h["Area"] == "New Zealand"]
    df_h = df_h.drop(columns="Area")
    df_h["Variable"] = "National ERP"
    df_h["Scenario"] = "Historical"

    latest_historical = df_h["Year"].max()

    # get projections
    df_p = pd.read_csv(projections_file)
    # ensure user-selected scenario exists
    if scenario not in df_p["Scenario"].unique():
        raise ValueError(
            f"The '{scenario}' scenario does not exist in population projections data"
        )

    df_p = df_p[df_p["Year"] > latest_historical]
    df_p = df_p[df_p["Scenario"] == scenario]

    # combine and create index
    df = pd.concat([df_h, df_p])
    base_value = df.loc[df["Year"] == base_year, "Value"].iloc[0]
    df["Index"] = df["Value"] / base_value
    df = df[["Year", "Variable", "Index"]].copy()
    # labelling
    df["Variable"] = "National population growth index"
    df["Scenario"] = scenario

    return df
