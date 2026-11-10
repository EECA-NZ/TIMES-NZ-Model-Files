"""Pure helpers for the machine-readable MBIE Energy Balance data."""

import pandas as pd


def select_gross_pj(data: pd.DataFrame, year: int) -> pd.DataFrame:
    """Select one calendar year's gross-PJ balance rows."""
    return data[(data["Year"] == year) & (data["Unit"] == "Gross PJ")].copy()


def get_balance_value(data: pd.DataFrame, entry: str, fuel: str) -> float:
    """Return one balance value, rejecting missing or ambiguous matches."""
    value = data.loc[(data["Entry"] == entry) & (data["Fuel"] == fuel), "Value"]
    if len(value) != 1:
        raise ValueError(
            f"Expected one balance value for entry={entry!r}, fuel={fuel!r}; "
            f"found {len(value)}."
        )
    return float(value.iloc[0])
