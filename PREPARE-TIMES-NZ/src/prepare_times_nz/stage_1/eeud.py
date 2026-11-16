"""Pure transformations for EEUD stage-1 inputs."""

import pandas as pd


def append_unallocated_onsite_generation(
    eeud: pd.DataFrame, onsite: pd.DataFrame
) -> pd.DataFrame:
    """Append MBIE's unallocated onsite electricity generation to EEUD in TJ."""
    required_columns = {"Year", "Value", "Unit"}
    missing_columns = required_columns - set(onsite.columns)
    if missing_columns:
        raise ValueError(
            "Unallocated onsite generation is missing columns: "
            + ", ".join(sorted(missing_columns))
        )
    if not onsite["Unit"].eq("PJ").all():
        raise ValueError("Unallocated onsite generation must use PJ")
    if onsite["Year"].duplicated().any():
        raise ValueError("Unallocated onsite generation has duplicate years")

    onsite = onsite[onsite["Year"].isin(eeud["Year"].unique())].copy()
    patch = pd.DataFrame(
        {
            "SectorGroup": "Industrial",
            "Sector": "Industrial - Unallocated",
            "SectorANZSIC": "Z003",
            "FuelGroup": "Electricity",
            "Fuel": "Electricity",
            "TechnologyGroup": "Unallocated",
            "Technology": "Unallocated",
            "EnduseGroup": "Unallocated",
            "EndUse": "Unallocated",
            "Transport": "Non-Transport",
            "Year": onsite["Year"],
            "Unit": "TJ",
            "Value": onsite["Value"] * 1e3,
        }
    )
    return pd.concat([eeud, patch[eeud.columns]], ignore_index=True)
