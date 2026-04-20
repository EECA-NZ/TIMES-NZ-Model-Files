"""Build tech capacity uptake inputs for Scen_Base_Constraints."""

import pandas as pd
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.filepaths import ASSUMPTIONS, STAGE_4_DATA
from prepare_times_nz.utilities.logger_setup import blue_text, logger

# CONSTANTS -----------------------
TECH_CAPACITY_UPTAKES_FILE = ASSUMPTIONS / "settings/tech_capacity_uptakes.csv"
OUTPUT_DIR = STAGE_4_DATA / "sys_settings"
OUTPUT_FILE = "capacity_uptake.csv"


# Functions --------------------------------------
def read_tech_capacity_uptakes(filepath=TECH_CAPACITY_UPTAKES_FILE):
    """
    Read tech capacity uptake assumptions from CSV.

    CSV expects columns:
      - TechName
      - NCAP_BND
      - NCAP_BND~0

    Label is optional and used only for logging.
    """
    df = pd.read_csv(filepath)
    required_columns = {
        "Attribute",
        "Pset_PN",
        "Pset_CI",
        "Pset_CO",
        "Cset_CN",
        "Other_Indexes",
        "Year",
        "LimType",
        "Value",
    }

    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(
            f"{filepath} is missing required columns: {sorted(missing_columns)}"
        )
    # Ensure Year is full number not integer for consistency
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")

    if "Label" in df.columns:
        for _, row in df.iterrows():
            logger.info(
                "Capacity uptake for %s (%s)",
                blue_text(row["Label"]),
                row["Pset_PN"],
            )

    return df


def create_capacity_uptake_table(df):
    """
    Trim the raw assumptions file to the VEDA columns used by FI_T.
    """
    return df[
        [
            "Attribute",
            "Pset_PN",
            "Pset_CI",
            "Pset_CO",
            "Cset_CN",
            "Other_Indexes",
            "Year",
            "LimType",
            "Value",
        ]
    ].copy()


def main():
    """Entry point."""
    df = read_tech_capacity_uptakes()
    df = create_capacity_uptake_table(df)

    _save_data(
        df,
        name=OUTPUT_FILE,
        label="Saving tech capacity uptakes",
        filepath=OUTPUT_DIR,
    )


if __name__ == "__main__":
    main()
