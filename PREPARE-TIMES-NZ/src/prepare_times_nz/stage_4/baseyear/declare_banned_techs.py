"""
This module identifies all base year processes that cannot be built in future years

They are defined as:
a) all electricity techs
b) any techs with null invcosts from all other baseyear parameters

These are then inserted into a ban table in the BY_TRANS file with NCAP_BND~0 = 2
We currently use wildcards as inputs so must register TFM_INS not TFM_DINS

Previously, we set NCAP_BND = 0 and NCAP_BND~0 = 5 in FI_T tables
But this did not seem to register properly for future years
"""

import pandas as pd
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.filepaths import STAGE_4_DATA
from prepare_times_nz.utilities.logger_setup import blue_text, logger

# CONSTANTS -----------------------

# just the ban list. the labels are just for the log/clarity:
# only the code is important for TIMES

baseyear_techs_to_ban = {
    "ELC_*": "All electricity",
    "RES*COA**": "Residential coal",
    "RES*WOD*": "Residential wood",
    "T_F*PET*": "Light petrol trucks",
    "T_P_B*PET*": "Petrol buses",
    "T_P_B*LPG*": "LPG buses",
    "C_WSR-SH-DirectH-GEO": "Commercial geothermal",
}


# Functions --------------------------------------
def register_codes_to_ban(code_dict):
    """
    Convert input dict to list of codes
    And output clear labels for what techs are banned
    """
    codes = []
    for code, label in code_dict.items():
        logger.info("Banning %s (%s)", blue_text(label), code)
        codes.append(code)

    df = pd.DataFrame()
    df["TechName"] = codes

    return df


def create_ban_table(df):
    """
    Takes the single variable input of codes to ban and creates
    the tfm_ins table
    Expects input df to have TechName, which is converted to Pset_PN
    """

    df["Attribute"] = "NCAP_BND"
    df["PSet_PN"] = df["TechName"]
    df["Year"] = 0
    df["Value"] = 2

    df = df[["Attribute", "PSet_PN", "Year", "Value"]]

    return df


def main():
    """
    Entry point
    """
    df = register_codes_to_ban(baseyear_techs_to_ban)
    df = create_ban_table(df)

    _save_data(
        df,
        name="banned_techs.csv",
        label="Saving banned base year techs",
        filepath=STAGE_4_DATA / "syssettings",
    )


if __name__ == "__main__":
    main()
