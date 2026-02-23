"""
This module exists because the transport demand data doesn't
     follow the same structure as other sectors
    And the categories are not included in the prepared staging data
    We recreate them here

Ideally, the prep methods would align with other sectors and
     we wouldn't need to double-handle this
"""

import numpy as np
import pandas as pd
from times_nz_internal_qa.utilities.filepaths import (
    CONCORDANCE_PATCHES,
    PREP_STAGE_4,
)

TRANSPORT_CONCORDANCES = CONCORDANCE_PATCHES / "transport"


def make_transport_concordance_patch():
    """
    An older function used to map technames and techs.
    We've just saved the outputs of this so its a bit clearer
    Can adjust or move the method later.
    """

    df_base = pd.read_csv(PREP_STAGE_4 / "base_year_tra/tra_process_parameters.csv")
    df_base = df_base[["TechName"]].drop_duplicates()

    df_new = pd.read_csv(PREP_STAGE_4 / "subres_tra/future_transport_processes.csv")
    df_new = df_new[["TechName"]].drop_duplicates()

    df = pd.concat([df_base, df_new])

    df["Utilisation"] = np.select(
        [
            df["TechName"].str.endswith("LOW"),
            df["TechName"].str.endswith("MED"),
            df["TechName"].str.endswith("HIGH"),
        ],
        ["Low", "Medium", "High"],
        default="All",
    )

    df["Technology"] = np.select(
        [
            df["TechName"].str.contains("ICEPET"),  # ICE (Petrol)
            df["TechName"].str.contains("ICEDSL"),  # ICE (Diesel)
            df["TechName"].str.contains("ICELPG"),  # ICE (LPG)
            df["TechName"].str.contains("BEV"),  # Battery Electric Vehicle
            df["TechName"].str.contains("HYBPET"),  # Hybrid (Petrol)
            df["TechName"].str.contains("HYBDSL"),  # Hybrid (Diesel)
            df["TechName"].str.contains("FCH2R"),  # Hydrogen fuel cell
            df["TechName"].str.contains("HEVPET"),  # PHEV (Petrol)
            df["TechName"].str.contains("HEVDSL"),  # PHEV (Diesel)
            df["TechName"].str.contains("SHIP"),  # Ship
            df["TechName"].str.contains("Jet"),  # Jet
            df["TechName"].str.contains("Rail"),  # Rail
        ],
        [
            "Internal Combustion Engine (Petrol)",
            "Internal Combustion Engine (Diesel)",
            "Internal Combustion Engine (LPG)",
            "Battery Electric Vehicle",
            "Hybrid Vehicle (Petrol)",
            "Hybrid Vehicle (Diesel)",
            "Hydrogen Fuel Cell",
            "Plug-in Hybrid Vehicle (Petrol)",
            "Plug-in Hybrid Vehicle (Diesel)",
            "Ship",
            "Jet",
            "Rail",
        ],
        default="Missing",
    )

    df["TechnologyGroup"] = np.select(
        [
            df["Technology"] == "Internal Combustion Engine (Petrol)",
            df["Technology"] == "Internal Combustion Engine (Diesel)",
            df["Technology"] == "Internal Combustion Engine (LPG)",
            df["Technology"] == "Battery Electric Vehicle",
            df["Technology"] == "Hybrid Vehicle (Petrol)",
            df["Technology"] == "Hybrid Vehicle (Diesel)",
            df["Technology"] == "Hydrogen Fuel Cell",
            df["Technology"] == "Plug-in Hybrid Vehicle (Petrol)",
            df["Technology"] == "Plug-in Hybrid Vehicle (Diesel)",
            df["Technology"] == "Ship",
            df["Technology"] == "Jet",
            df["Technology"] == "Rail",
        ],
        [
            "Internal Combustion Engine",
            "Internal Combustion Engine",
            "Internal Combustion Engine",
            "Battery Electric Vehicle",
            "Hybrid Vehicle",
            "Hybrid Vehicle",
            "Hydrogen Vehicle",
            "Plug-in Hybrid Vehicle",
            "Plug-in Hybrid Vehicle",
            "Ship",
            "Jet",
            "Rail",
        ],
        default="Missing",
    )

    df.to_csv(TRANSPORT_CONCORDANCES / "processes.csv", index=False)


def main():
    """entrypoint"""
    make_transport_concordance_patch()


if __name__ == "__main__":
    make_transport_concordance_patch()
