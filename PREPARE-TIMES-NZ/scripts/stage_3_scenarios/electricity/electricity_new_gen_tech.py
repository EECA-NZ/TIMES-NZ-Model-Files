"""
New Tech Data manipulation
new_tech_data.py
This scripts purpose is to build a table of data for the
new electricity generating technology that is found in the MBIE GenStack data.
It adds additional datasets for offshore wind and distributed residential solar


It then applies learning curves to the costs for future plants

The data also contains some  offshore wind data from NREL and
uses the learning curves obtained from the NREL ATB data to produce learning curves
for the CAPEX and FOM of new solar, wind, and geothermal.
It also has data on the capacities, whether the plant has a fixed or
earliest commissioning year or if it is able to be commissioned at any time.
"""

# Getting Custom Libraries


import numpy as np
import pandas as pd
from prepare_times_nz.utilities.deflator import deflate_data
from prepare_times_nz.utilities.filepaths import (
    ASSUMPTIONS,
    CONCORDANCES,
    DATA_RAW,
    STAGE_1_DATA,
    STAGE_3_DATA,
)
from prepare_times_nz.utilities.logger_setup import logger

# CONSTANTS ----------------------------------------------------------------

BASE_YEAR = 2023
# set the expansion to 2050.
# this will likely just align with the last NREL year anyway.
years_used = list(range(BASE_YEAR, 2051))

# USD to NZD exchange rate
EXCHANGE_RATE_USD = 0.62

# Filepath shortcuts
FUTURE_TECH_ASSUMPTIONS = ASSUMPTIONS / "electricity_generation/future_techs"
OUTPUT_LOCATION = STAGE_3_DATA / "electricity"

# script settings
pd.set_option("future.no_silent_downcasting", True)

# GET DATA ------------------------------------
genstack_file = pd.read_csv(f"{STAGE_1_DATA}/mbie/gen_stack.csv")
nrel_data = pd.read_csv(f"{STAGE_1_DATA}/nrel/future_electricity_costs.csv")

census_dwellings = pd.read_csv(
    f"{DATA_RAW}/external_data/statsnz/census/total_dwellings.csv"
)
region_to_island = pd.read_csv(f"{CONCORDANCES}/region_island_concordance.csv")
new_tech = pd.read_csv(f"{FUTURE_TECH_ASSUMPTIONS}/NewTechnology.csv")
tracked_solar = pd.read_csv(f"{FUTURE_TECH_ASSUMPTIONS}/TrackingSolarPlants.csv")


# FUNCTIONS -------------------------------


def get_commissioning_year_type(row):
    """
    Inspects a row of a dataframe
    Expects variables:
     - Fixed Commissioning Year
     - Earliest Commissioning Year

    Defines the commissioning year type based on whether these values have data

    """
    # names of the MBIE variables
    fixed = row["Fixed Commissioning Year"]
    early = row["Earliest Commissioning Year"]

    # Check if col1 has a non-zero/non-null value
    if pd.notnull(fixed) and fixed != 0:
        return "Fixed"
    # col1 is blank or zero, check col2
    if pd.notnull(early) and early != 0:
        return "Earliest year"
    # else
    return "Any year"


def load_genstack():
    """
    Get the genstack data and reshape the commissioning year variables
    """
    # filter to scenario
    # df = genstack_file[genstack_file["Scenario"] == scenario]
    df = genstack_file.copy()
    df = df[df["Status"] != "Current"]

    # Assign commissioning year to a single variable and add a YearType

    df["CommissioningType"] = df.apply(get_commissioning_year_type, axis=1)
    df["CommissioningYear"] = df["Fixed Commissioning Year"].fillna(
        df["Earliest Commissioning Year"]
    )

    # dropping the now unwanted columns
    cols_to_drop = ["Fixed Commissioning Year", "Earliest Commissioning Year"]
    df = df.drop(columns=[col for col in cols_to_drop if col in df.columns])

    # we specify the year (our base year)
    df["Year"] = BASE_YEAR
    return df


def reshape_genstack(df):
    """

    take the loaded genstack and pivot/reshape the variables long
    easier to work with

    """
    # pivot and rename

    # manual mapping of genstack variable names to new variable names and units
    genstack_vars = {
        "Capacity (MW)": ["Capacity", "MW"],
        "Heat Rate (GJ/GWh)": ["HeatRate", "GJ/GWh"],
        "Variable operating costs (NZD/MWh)": ["VAROM", "NZD/MWh"],
        "Fixed operating costs (NZD/kW/year)": ["FOM", "NZD/kW/year"],
        "Fuel delivery costs (NZD/GJ)": ["FuelDeliveryCost", "NZD/GJ"],
        "Capital cost (NZD/kW)": ["CAPEX", "NZD/kW"],
        "Connection cost (NZD $m)": ["ConnectionCost", "NZD $m"],
        "Total Capital costs (NZD $m)": ["CAPEX_incl_connection", "NZD $m"],
    }

    values_to_pivot = genstack_vars.keys()

    id_vars = [col for col in df.columns if col not in values_to_pivot]

    df = df.melt(
        id_vars=id_vars,
        value_vars=values_to_pivot,
        var_name="OriginalVariable",
        value_name="Value",
    )

    # map the units and variables to the original variable name
    df[["Variable", "Unit"]] = df["OriginalVariable"].map(genstack_vars).tolist()
    # no longer needed
    df = df.drop("OriginalVariable", axis=1)
    # we don't need this - will recreate later.
    # could also have just dropped the column earlier then not mapped
    df = df[df["Variable"] != "CAPEX_incl_connection"]

    return df


def define_genstack_learning_curves(df):
    """
    This simply applies our logic to create a boolean for each plant
    This boolean is later used to decide whether to apply learning curves
    """

    # define plants to create learning curves for
    mask = (
        # only wind/solar/geo
        df.Tech.isin(["Wind", "Solar", "Geo"])
        # only if not commissioned before 2030
        & ((df["CommissioningYear"] >= 2030) | (df["CommissioningType"] == "Any year"))
        # and not applied to stuff already consented/under construction.
        # Assume costs remain for these
        & ~df.Status.isin(["Fully consented", "Under construction"])
    )

    df["AddLearningCurve"] = np.where(mask, True, False)

    return df


def get_learning_curves(index_year=BASE_YEAR):
    """
    We use the NREL data for CAPEX and FOM to derive indexed learning curves
    for every NREL technology
    They're indexed to the base year by default
    """

    group_vars = ["Technology", "Scenario", "Variable"]

    df = nrel_data.copy()
    # base year is earliest year
    df = df[df["Year"] >= index_year]

    # sort to ensure index works
    df = df.sort_values(group_vars + ["Year"])
    # create index
    df["Index"] = df.groupby(group_vars)["Value"].transform(lambda x: x / x.iloc[0])

    # select only relevant vars
    df = df[group_vars + ["Year", "Index"]]

    df = df.rename(columns={"Scenario": "NRELScenario"})

    return df


def expand_genstack_years(df):
    """
    Takes the input genstack, which should have one row for each plant
    Expands this to cover the full year range so that we can apply our learning curves

    """

    # check that the grain is appropriate per plant
    if df.groupby("Plant")["Year"].nunique().gt(1).any():
        raise ValueError("Some plants have multiple year entries: please review")

    # expand
    df = df.drop("Year", axis=1)
    year_list = pd.DataFrame({"Year": years_used})
    df = df.merge(year_list, how="cross")

    return df


def apply_learning_curves(df):
    """
    Expects the tidy genstack input as a df

    Removes the plants where we don't want to apply learning curves
    and the variables we don't want to apply curves to

    applies the learning curves based on NREL index,
    Then adds the old data back to the main dataframe

    The variables that get curves MUST be labelled in the NREL data inputs
    Those variable labels were defined in the Stage 1 NREL extraction script

    They are currently:
        CAPEX

        FOM

    """
    # define data to curve
    vars_to_learn = ["CAPEX", "FOM"]
    curve_mask = df["AddLearningCurve"] & df["Variable"].isin(vars_to_learn)

    # keep the uncurved for later
    df_inapplicable = df.loc[~curve_mask].copy()

    # get only rows to apply curves to
    df = df.loc[curve_mask]
    # expand across full year series
    df = expand_genstack_years(df)

    # get nrel curves
    nrel = get_learning_curves()
    # map the techs to the relevant NREL column
    logger.warning("NREL tech mapping for genstack hardcoded in this script")
    nrel_tech_mapping = {
        "Utility PV - Class 1": "Solar",
        "Land-Based Wind - Class 2 - Technology 1": "Wind",
        "Geothermal - Hydro / Flash": "Geo",
    }
    nrel["Tech"] = nrel["Technology"].map(nrel_tech_mapping)
    # filter and shape
    nrel = nrel[~nrel["Tech"].isna()]
    nrel = nrel[["NRELScenario", "Tech", "Variable", "Year", "Index"]]

    # join curves to main data (with curve mask)
    df = df.merge(nrel, how="left")
    # apply index to costs for each var (probably CAPEX + FOM)
    df["Value"] = df["Value"] * df["Index"]

    # add back non-curved data
    df = pd.concat([df, df_inapplicable])
    df = df.drop(["AddLearningCurve", "Index"], axis=1)
    return df


def recalculate_capex(df):
    """
    Takes the genstack
    Recalculates a weighted capex by adding the ConnectionCost to CAPEX
    Returns genstack having removed ConnectionCost and increased CAPEX

    input df must contain a long "Variable" columns which contains:
        "ConnectionCost"
        "Capacity"
        "CAPEX"
    df must also contain a "Unit" field

    Function will fail if "Unit" does not match expectations for:
        Capacity
        ConnectionCost

    """

    def get_quick_genstack_var(df, variable):
        df = df[df["Variable"] == variable]
        unit = df["Unit"].iloc[0]
        variable_unit = f"{variable} - {unit}"
        df = df.rename(columns={"Value": variable_unit})
        df = df[["Scenario", "Plant", variable_unit]]
        return df

    # calculate weighted connection cost per plant/scenario
    #
    w_conn = pd.merge(
        get_quick_genstack_var(df, "Capacity"),
        get_quick_genstack_var(df, "ConnectionCost"),
        on=["Scenario", "Plant"],
    )
    w_conn["WeightedConnection"] = (
        w_conn["ConnectionCost - NZD $m"] / w_conn["Capacity - MW"]
    )
    # $m / MW convert to NZD/kW
    w_conn["WeightedConnection"] = w_conn["WeightedConnection"] * 1e3

    # add "CAPEX" variable and use to join to main
    # create a capex table to manipulate
    df_capex = df[df["Variable"] == "CAPEX"]
    df_capex = df_capex.merge(w_conn, how="left")

    # nulls must be 0
    df_capex["WeightedConnection"] = df_capex["WeightedConnection"].fillna(0)
    # add to main
    df_capex["Value"] = df_capex["Value"] + df_capex["WeightedConnection"]
    # just take original columns

    df_capex = df_capex[df.columns]

    # remove original capex and add new
    df_no_capex = df[df["Variable"] != "CAPEX"]
    df = pd.concat([df_no_capex, df_capex])

    return df


def distinguish_tracking_solar(df):
    """
    Changes the Tech and TechName field for solar plants
    Uses an assumption file as input which contains names of Tracking plants

    The rest are defined as Fixed solar

    """
    # Update tracking plants
    df.loc[df["Plant"].isin(tracked_solar), "Tech"] = "SolarTracking"
    df.loc[df["Plant"].isin(tracked_solar), "TechName"] = "Solar (Tracking)"

    # Update the remaining solar plants to fixed
    df.loc[(df["Tech"] == "Solar") & (~df["Plant"].isin(tracked_solar)), "Tech"] = (
        "SolarFixed"
    )
    df.loc[
        (df["TechName"] == "Solar") & (~df["Plant"].isin(tracked_solar)), "TechName"
    ] = "Solar (Fixed)"

    return df


def get_genstack():
    """
    Wrapper for our genstack manipulation functions.
    1) Load the genstack (and reshape the commyear variables)
    2) Pivot wide add unit vars
    3) Define plants to add learning curves to
    4) Apply learning curves for CAPEX and FOM to those plants
    5) recalculate total capex NZD/kW
         (using reduced capex + weighted connection cost)
    6) Adjusts solar techs based on fixed/tracking
    Returns df
    """

    df = load_genstack()
    df = reshape_genstack(df)
    df = define_genstack_learning_curves(df)
    df = apply_learning_curves(df)
    df = recalculate_capex(df)
    df = distinguish_tracking_solar(df)

    return df


def get_offshore_wind():
    """
    1: Get NREL data
    2: Filter to offshore wind
    3: deflate and convert NZD
    4: reshape to genstack expectations
    """
    # Get NREL offshore wind data
    offshore_wind_techs = ["Offshore Wind - Class 1", "Offshore Wind - Class 8"]
    df = nrel_data.copy()
    df = df[df["Technology"].isin(offshore_wind_techs)]

    # get new tech parameters for offshore from assumptions
    new_tech_offshore = new_tech[new_tech["Plant"].isin(offshore_wind_techs)]

    # removing any data from years before the base year
    df = df[df["Year"] >= BASE_YEAR]

    # join the assumption parameters for CAPEX/OPEX
    df = df.rename(columns={"Technology": "Plant", "Scenario": "NRELScenario"})
    map_offshore = new_tech[
        [
            "Plant",
            "Tech",
            "TechName",
            "Status",
            "Region",
            "CommissioningType",
            "CommissioningYear",
        ]
    ]
    df = pd.merge(df, map_offshore, on="Plant", how="inner")

    # add other variables from assumptions file
    df = pd.concat([df, new_tech_offshore])

    # add unit lables
    unit_map = {
        "Capacity": "MW",
        "Heat Rate": "GJ/GWh",
        "VOC": "$/MWh",
        "FOM": "$/kW",
        "FDC": "$/GJ",
        "CAPEX": "$/kW",
    }
    df["Unit"] = df["Variable"].map(unit_map)

    df_to_deflate = df[~df["PriceBaseYear"].isna()]

    deflated = deflate_data(
        df_to_deflate, variables_to_deflate=["Value"], base_year=BASE_YEAR
    )
    # USD/NZD conversion
    deflated["Value"] = deflated["Value"] / EXCHANGE_RATE_USD
    # add deflated data to other variables (ie old df with no PriceBaseYear)
    df = pd.concat([deflated, df[df["PriceBaseYear"].isna()]])

    df = df.drop("PriceBaseYear", axis=1)

    return df


def get_residential_solar():
    """
    Builds and calculates residential solar future tech parameters

    Note: this repeats a lot of the methods used for other plants
    However, they're not using the same functions - could generalise methods.

    """

    # get dsolar assumptions
    dsolar = new_tech[new_tech["TechName"] == "Residential dist solar"]
    capex = dsolar[dsolar["Variable"] == "CAPEX"]
    fom = dsolar[dsolar["Variable"] == "FOM"]
    capacity = dsolar[dsolar["Variable"] == "Capacity"]

    # this list defines which variables we add back later
    # they should match the input assumption fields
    parameters = [
        "Plant",
        "PlantType",
        "Tech",
        "TechName",
        "Status",
        "CommissioningType",
        "CommissioningYear",
        "Variable",
        "Unit",
    ]

    # get total dwelling counts
    dwellings = census_dwellings[census_dwellings["Census year"] == "2023"]
    dwellings = dwellings[
        ~dwellings["Region"].isin(
            ["North Island", "South Island", "Chatham Islands", "New Zealand"]
        )
    ]

    # Estimate max capacity per region
    # uses current dwelling count and share/unit capacity assumptions
    house_share = dsolar[dsolar["Variable"] == "MaxShareOfHouses"]["Value"].iloc[0]
    solar_cap = dsolar[dsolar["Variable"] == "Capacity"]["Value"].iloc[0]
    df = dwellings[["Region", "Value"]].copy()
    df["Value"] = df["Value"] * house_share * solar_cap
    # re-add parameters from input assumptions
    df = pd.merge(df, capacity[parameters], how="cross")

    # apply curves to capex (not fom)
    nrel = get_learning_curves()
    # this nrel renaming is repeated unfortunately - could refactor out somehow
    nrel = nrel.rename(columns={"Technology": "Plant", "Scenario": "NRELScenario"})
    capex = capex.merge(nrel, on=["Plant", "Variable"], how="left")
    capex["Value"] = capex["Value"] * capex["Index"]
    capex = capex.drop("Index", axis=1)

    # combine costs with cap and fom
    df = pd.concat([df, capex, fom])

    # set default year
    df["Year"] = df["Year"].fillna(BASE_YEAR)

    return df


def main():
    """

    Pulls the three component pieces
        genstack
        offshore wind
        residential solar
    combines these parameters and saves to staging
    """
    OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)

    genstack = get_genstack()
    offshore_wind = get_offshore_wind()
    res_solar = get_residential_solar()
    df = pd.concat([genstack, offshore_wind, res_solar])

    filename = OUTPUT_LOCATION / "future_generation_tech.csv"
    logger.info("Saving future tech data to %s", filename)
    df.to_csv(filename, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
