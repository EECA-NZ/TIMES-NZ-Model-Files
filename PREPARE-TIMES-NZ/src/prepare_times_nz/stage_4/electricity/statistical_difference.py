"""
Transform MBIE electricity-demand totals into stat differences.
Compares observed to calculated GWh and converts to PJ
Carries forward latest year.
Applies as fake demand to ensure elec system balance.
parameterised share, set in coded assumptions
"""

import pandas as pd


def create_statistical_difference_parameters(
    electricity_demand_totals: pd.DataFrame,
    share_of_statdiff_demand: float,
    base_year: int,
) -> pd.DataFrame:
    """Create fixed demand from a share of MBIE's calculated-demand gap."""
    data = electricity_demand_totals.loc[
        electricity_demand_totals["Year"] >= base_year,
        ["Year", "CalculatedDemandGWh", "ObservedDemandGWh"],
    ].copy()
    data["StatisticalDifferenceGWh"] = (
        data["CalculatedDemandGWh"] - data["ObservedDemandGWh"]
    )
    if (
        data.empty
        or data["Year"].duplicated().any()
        or data["StatisticalDifferenceGWh"].lt(0).any()
    ):
        raise ValueError(
            "Statistical-difference data must contain one non-negative row per model year"
        )

    data["Value"] = data["StatisticalDifferenceGWh"] * share_of_statdiff_demand * 0.0036
    output = data.set_index("Year")["Value"].to_frame().T
    output.columns = [f"ACT_BND~FX~{year}" for year in output.columns]
    output.insert(0, "Comm-IN", "ELC")
    output.insert(0, "TechName", "StatDiffDemand_ELC")
    output["ACT_BND~FX~0"] = 5
    return output
