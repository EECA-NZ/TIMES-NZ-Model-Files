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
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.filepaths import ASSUMPTIONS, STAGE_4_DATA

input_file = ASSUMPTIONS / "electricity_generation/renewable_curves/RenewableCurves.csv"


OUTPUT_LOCATION = STAGE_4_DATA / "scen_ren_af"


def generate_ren_af_file():
    """
    Mostly just reads in the assumptions, relabels
    Assigns wildcards based on the TechCode which should be in all our technames
    already (but this could be tidied up a bit)

    Includes logic on fixed v upper limit AFs (controlling spill)
    """

    # read data
    df = pd.read_csv(input_file)

    # define all the techs with fixed af codes - other techs get "upper" (ie wind/hydro)
    # this is another way of saying we expect wind to spill first if we're in a spill situation
    # (or that solar/geo don't spill)
    fixed_af_techs = ["Geo", "SolarDist", "SolarTracking", "SolarFixed"]

    # additional requirements
    df["LimType"] = np.where(df["TechCode"].isin(fixed_af_techs), "FX", "UP")
    df["Attribute"] = "NCAP_AF"

    # generate wildcards
    df["Pset_PN"] = "ELC_*" + df["TechCode"] + "*"

    # trim to necessary columns
    df = df[["TimeSlice", "LimType", "Attribute", "NI", "SI", "Pset_PN"]]

    return df


def main():
    """script wrapper"""
    df = generate_ren_af_file()
    _save_data(
        df,
        "renewable_availability.csv",
        "Renewable availability curves",
        OUTPUT_LOCATION,
    )


if __name__ == "__main__":
    main()
