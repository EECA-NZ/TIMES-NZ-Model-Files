"""

Ok, so here we assign a TIMES code to define each process.

This should be a unique combination of sector, tech, fuel, and use, GENERALLY speaking

What this means is that - because that is already the grain of the data - users cannot swap techs for different output requirements

Then the output commodity should be a unique combination of sector, tech, and use

What this means, by default, is that because the commodity is not defined by the fuel, any tech (regardless of fuel) is able to provide it, so the model can choose different fuels
but not techs.

However, because the process is defined by the fuel, I can't by default just put biomass in my coal boiler. I'd need to buy a biomass boiler
By default, we have no dual fuel inputs

This covers the vast majority of our use cases. However, it means that I can't swap between boilers, resistance heaters, or heat pumps for my space heating.
So we would need to tweak that. There may be other areas we want to tweak.

Current tweaks to default mapping:

1) Feedstock is not assigned the industry use of the fuel. That's because this is combusted and contributes to energy emissions
    - In reality, feedstock is either not combusted, or its combustion emissions contribute to IPPU, not energy emissions
2) Space heating is "technology agnostic"
    - This means any space heating demand could be met by resistance heaters, heat pumps, or whatever else we have. Process heating is more specific so we are not agnostic.




"""

# Libraries etc

import os

import numpy as np
import pandas as pd
from prepare_times_nz.filepaths import CONCORDANCES, STAGE_2_DATA
from prepare_times_nz.logger_setup import blue_text, logger

# Constants -----------------------------------------
run_tests = True

# Filepaths -----------------------------------------

output_location = f"{STAGE_2_DATA}/industry/preprocessing"
os.makedirs(output_location, exist_ok=True)

checks_location = f"{STAGE_2_DATA}/industry/checks/4_process_commodity_definitions"
os.makedirs(checks_location, exist_ok=True)

INDUSTRY_CONCORDANCES = f"{CONCORDANCES}/industry"

# Get data ------------------------------
# process and commmodity name definitions - these are used to build the final codes in a structured way

df = pd.read_csv(f"{output_location}/3_times_baseyear_with_assumptions.csv")

use_codes = pd.read_csv(f"{INDUSTRY_CONCORDANCES}/use_codes.csv")
tech_codes = pd.read_csv(f"{INDUSTRY_CONCORDANCES}/tech_codes.csv")
sector_codes = pd.read_csv(f"{INDUSTRY_CONCORDANCES}/sector_codes.csv")
fuel_codes = pd.read_csv(f"{INDUSTRY_CONCORDANCES}/fuel_codes.csv")


# Functions -----------------------------------------


def save_output(df, name):

    filename = f"{output_location}/{name}"
    logger.info(f"Saving output:\n{blue_text(filename)}")
    df.to_csv(filename, index=False)


def save_checks(df, name, label):
    filename = f"{checks_location}/{name}"
    logger.info(f"Saving {label}:\n{blue_text(filename)}")
    df.to_csv(filename, index=False)


def check_missing_times_codes(df, varname):

    # define the TIMES code variable name to check
    varname_times = f"{varname}_TIMES"
    # see if there are any missing
    df = df[df[varname_times].isna()]
    # return all the original items with no join
    missing_codes = df[[varname, varname_times]].drop_duplicates()
    missing_count = len(missing_codes)
    # report
    if missing_count > 0:
        logger.warning(
            f"Warning: the following {missing_count} '{varname}' items have no TIMES code equivalent"
        )

        for (
            index,
            row,
        ) in missing_codes.iterrows():
            logger.warning(f"        {row[varname]}")

        logger.warning(
            f"This will lead to issues: please check the input concordance file and ensure you have full '{varname}' coverage"
        )
    else:
        logger.info(f"Full {varname} code coverage found")


def add_times_codes(df, code_mapping, varname):
    df = pd.merge(df, code_mapping, on=varname, how="left")
    if run_tests:
        check_missing_times_codes(df, varname)
    return df


def define_process_commodities(df):

    # define original columns
    original_columns = list(df.columns)

    # first add all our codes
    df = add_times_codes(df, use_codes, "EndUse")
    df = add_times_codes(df, tech_codes, "Technology")
    df = add_times_codes(df, sector_codes, "Sector")
    df = add_times_codes(df, fuel_codes, "Fuel")

    # we can use these to build up the generated names for each process and commodity.

    # default process and commodity definitions
    df["Process"] = df[
        ["Sector_TIMES", "Fuel_TIMES", "Technology_TIMES", "EndUse_TIMES"]
    ].agg("-".join, axis=1)
    df["CommodityIn"] = "IND" + df[["Fuel_TIMES"]].agg("-".join, axis=1)
    df["CommodityOut"] = df[["Sector_TIMES", "Technology_TIMES", "EndUse_TIMES"]].agg(
        "-".join, axis=1
    )

    # Adjustments: Feedstock is not IND (because IND fuels are combusted, we would overcount emissions)
    # even when the coal IS combusted, it is IPPU, so we leave this hanging for now
    df["CommodityIn"] = np.where(
        df["EndUse"] == "Feedstock", df["Fuel_TIMES"], df["CommodityIn"]
    )
    logger.info("Adjusting feedstock to not use industrial fuel commodities")

    # Adjustments: SpaceHeating does not need tech to define the commodity.
    # Effectively, we are saying any SH use can be met within a sector by any tech, not just any tech/fuel
    # we first derive this special tech-agnostic output commodity
    df["CommodityOutTechAgnostic"] = df[["Sector_TIMES", "EndUse_TIMES"]].agg(
        "-".join, axis=1
    )

    # and use it to overwrite all our commodities if the end use is space heating
    df["CommodityOut"] = np.where(
        df["EndUse"] == "Low Temperature Heat (<100 C), Space Heating",
        df["CommodityOutTechAgnostic"],
        df["CommodityOut"],
    )
    logger.info("Allowing space heating demand to use any space heating technology")

    # Potential adjustments: we do not yet allow for any dual-fuel boilers
    # The future techs allow for dual-fuel wood/biomass boilers (either bought or repurposed from existing coal boilers)
    # However, we are declaring the existing boilers are all either wood or coal, not both.
    # This could be changed later potentially - if so it should be done here.

    # Finally, clean up. We just want our original columns plus the process and commodity in/out definitions
    df = df[["Process", "CommodityIn", "CommodityOut"] + original_columns]

    return df


def make_wide(df):

    df["Variable"] = df["Variable"] + " (" + df["Unit"] + ")"

    df = df.drop("Unit", axis=1)

    id_cols = [col for col in df.columns if col not in ["Variable", "Value"]]

    df = df.pivot(index=id_cols, columns="Variable", values="Value").reset_index()

    return df


# Execute

df = define_process_commodities(df)
save_output(df, "4_times_baseyear_with_commodity_definitions.csv")

df_wide = make_wide(df)
save_checks(df_wide, "baseyear_with_commodities_wide.csv", "data in wide format")
