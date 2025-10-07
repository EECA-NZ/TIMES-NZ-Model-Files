"""
Rules for all electricity generating processes

Outputs a concordance file for these



"""

# get data
import pandas as pd
from times_nz_internal_qa.utilities.filepaths import (
    PREP_STAGE_2,
    PROCESS_CONCORDANCES,
)

# suggested labels:


# first read in the main one - we'll take some from this


def get_elc_base_processes():
    """
    Read all base year ele processes from staging prep data
    Return codes and categories
    """

    df = pd.read_csv(PREP_STAGE_2 / "electricity/base_year_electricity_supply.csv")
    df = df[["TechName", "PlantName", "Tech_TIMES"]].drop_duplicates()

    df = df.rename(columns={"TechName": "Process"})
    df["ProcessGroup"] = "Electricity generation"
    return df


def main():
    """
    Entry point. Simply reads and writes the base year elc processes.
    """
    df = pd.concat([get_elc_base_processes()])

    df.to_csv(
        PROCESS_CONCORDANCES / "elec_generation.csv", index=False, encoding="utf-8-sig"
    )


if __name__ == "__main__":
    main()
