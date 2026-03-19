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
from prepare_times_nz.utilities.filepaths import ASSUMPTIONS, STAGE_4_DATA
from prepare_times_nz.utilities.logger_setup import blue_text, logger

# CONSTANTS -----------------------

BANNED_TECHS_FILE = ASSUMPTIONS / "settings/banned_techs.csv"


# Functions --------------------------------------
def register_codes_to_ban(filepath=BANNED_TECHS_FILE):
    """
    Read banned tech codes from CSV and convert to ban table input format.

    CSV expects columns:
      - Code
      - Label

    And output clear labels for what techs are banned
    """
    df = pd.read_csv(filepath)
    required_columns = {"Code", "Label"}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(
            f"{filepath} is missing required columns: {sorted(missing_columns)}"
        )

    codes = []
    for _, row in df.iterrows():
        code = row["Code"]
        label = row["Label"]
        logger.info("Banning %s (%s)", blue_text(label), code)
        codes.append(code)

    out_df = pd.DataFrame()
    out_df["TechName"] = codes

    return out_df


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
    df = register_codes_to_ban()
    df = create_ban_table(df)

    _save_data(
        df,
        name="banned_techs.csv",
        label="Saving banned base year techs",
        filepath=STAGE_4_DATA / "sys_settings",
    )


if __name__ == "__main__":
    main()
