"""Shared helpers for stage 3 demand projection modules."""

import pandas as pd

VALID_ENERGY_VARIABLES = ("OutputEnergy", "InputEnergy")


def get_baseyear_demand(data_path, variable, location_column):
    """Load and aggregate base year demand for a selected energy variable."""
    if variable not in VALID_ENERGY_VARIABLES:
        raise ValueError(
            f"Invalid variable '{variable}'. Must be 'InputEnergy' or 'OutputEnergy'."
        )

    df = pd.read_csv(data_path)
    df = df[df["Variable"] == variable]
    return (
        df.groupby(
            [
                "Sector",
                "CommodityOut",
                location_column,
                "Technology",
                "EndUse",
                "Variable",
                "Unit",
            ]
        )["Value"]
        .sum()
        .reset_index()
    )
