"""

Reads the renewable curve input assumptions, generates wildcards, and relabels

Currently very simple
we might want to tidy up our tech code joining because right now it's messier than it needs to be!

Best to keep wildcards on techs rather than creating a DINS,
because the plant list might change between scenarios
and we don't want to be updating this every time we switch a scenario run


# potential to-do: get full list of plant outputs that match our existing plants


"""

import numpy as np
import pandas as pd
from prepare_times_nz.stage_0.stage_0_settings import BASE_YEAR
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.filepaths import (
    ASSUMPTIONS,
    CONCORDANCES,
    STAGE_2_DATA,
    STAGE_3_DATA,
    STAGE_4_DATA,
)

cap_factors = ASSUMPTIONS / "electricity_generation/CapacityFactors.csv"
generated_curves_file = STAGE_3_DATA / "electricity/renewable_curves.csv"

tech_codes = CONCORDANCES / "electricity/tech_codes.csv"


OUTPUT_LOCATION = STAGE_4_DATA / "scen_ren_af"


def generate_ren_af_file():
    """
    Mostly just reads in the assumptions, relabels
    Assigns wildcards based on the TechCode which should be in all our technames
    already (but this could be tidied up a bit)

    Includes logic on fixed v upper limit AFs (controlling spill)
    """

    # read data
    if not generated_curves_file.exists():
        raise FileNotFoundError(
            "Missing generated renewable curves at "
            f"{generated_curves_file}. Run the stage-3 solar build first."
        )

    df = pd.read_csv(generated_curves_file)

    if "TechCode" in df.columns:
        df = df.rename(columns={"TechCode": "Tech_TIMES"})

    # define all the techs with fixed af codes - other techs get "upper" (ie wind/hydro)
    # this is another way of saying we expect wind to spill first if we're in a spill situation
    # (or that solar/geo don't spill)
    fixed_af_techs = ["SolarDist", "SolarTrack", "SolarFixed"]

    # seasonal techs are those where we want flex within parent slices
    seasonal_af_techs = ["HydSC"]
    #

    # additional requirements
    df["LimType"] = np.where(df["Tech_TIMES"].isin(fixed_af_techs), "FX", "UP")

    # generate AFs (AFS for seasonal techs)
    df["Attribute"] = np.where(
        df["Tech_TIMES"].isin(seasonal_af_techs), "NCAP_AFS", "NCAP_AF"
    )

    # generate wildcards
    df["Pset_PN"] = "ELC_" + df["Tech_TIMES"] + "_*"

    # trim to necessary columns
    df = df[["TimeSlice", "LimType", "Attribute", "NI", "SI", "Pset_PN"]]

    return df


def generate_baseload_file():
    """
    Set AF for CHP plants as fixed across all slices
    This means baseload, effectively
    We'll do it for geo too

    """

    yrfr = pd.read_csv(STAGE_2_DATA / "settings/load_curves/yrfr.csv")

    slices = yrfr[["TimeSlice"]]

    cf = pd.read_csv(cap_factors)
    tc = pd.read_csv(tech_codes)

    codes = tc.merge(cf, on=["TechnologyCode", "FuelType"])

    # only cogen or geo capfactors
    codes = codes[(codes["TechnologyCode"] == "COG") | (codes["Tech_TIMES"] == "Geo")]

    codes = codes[["Tech_TIMES", "CapacityFactor"]].drop_duplicates()

    # expand to all timeslices
    #   note: reasonably sure this works the same if we don't expand
    #   and just leave timeslice blank, then each child slice inherits
    #   but making explicit for now just in case
    df = codes.merge(slices, how="cross")

    # labelling
    df["NI"] = df["CapacityFactor"]
    df["SI"] = df["CapacityFactor"]

    # everything fixed, except coalchp, because we're curving this off for EAF
    df["LimType"] = np.where(df["Tech_TIMES"] == "CoalCHP", "UP", "FX")
    df["Attribute"] = "NCAP_AF"

    # pset generation
    df["Pset_PN"] = "ELC_" + df["Tech_TIMES"] + "_*"

    # select key vars
    df = df[["TimeSlice", "LimType", "Attribute", "NI", "SI", "Pset_PN"]]

    # wildcard adjustment - want to ensure the geochp doesn't get confused
    # without this it seems to think ELC_Geo_* applies to ELC_Geo_CHP_*
    # which causes infeasibilities (both 80% and 95% availability constraints)
    # this is a bit hardcoded sorry

    df["Pset_PN"] = np.where(
        df["Pset_PN"] == "ELC_Geo_*", "ELC_Geo_*, -ELC_GeoCHP_*", df["Pset_PN"]
    )
    return df


def adjust_starting_year(df, year):
    """
    The renewable availability curves may be different from our
    Base year generation for various reasons
    We force the afs to start from a specific year
    and extrapolate forwards (not backwards)

    Usually this would just be for baseyear+1
    """
    # define value columns to apply extrapolation with later
    value_cols = ["NI", "SI"]

    interp_code = 5  # forward but not back

    df_main = df.copy()
    df_main["Year"] = year

    # interpolation/extrapolation
    df_ie = df.copy()
    df_ie["Year"] = 0
    for col in value_cols:
        df_ie[col] = interp_code

    out = pd.concat([df_main, df_ie])
    return out


def main():
    """script wrapper"""
    df_ren = generate_ren_af_file()
    df_baseload = generate_baseload_file()

    df = pd.concat([df_ren, df_baseload])

    out = adjust_starting_year(df, BASE_YEAR + 1)

    _save_data(
        out,
        "renewable_availability.csv",
        "Renewable availability curves",
        OUTPUT_LOCATION,
    )


if __name__ == "__main__":
    main()
