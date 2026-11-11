"""
Transform MBIE electricity-demand totals into stat differences.
Compares observed to calculated GWh and converts to PJ
Carries forward latest year.
Applies as fake demand to ensure elec system balance.
parameterised share, set in coded assumptions
"""

import pandas as pd


def calculate_island_electricity_shares(
    baseyear_demand_tables: list[pd.DataFrame],
) -> pd.Series:
    """Return base-year stationary electricity-input shares by island."""
    electricity_demand = []
    for table in baseyear_demand_tables:
        region_column = "Region" if "Region" in table.columns else "Island"
        electricity_demand.append(
            table.loc[
                (table["Fuel"] == "Electricity") & (table["Variable"] == "InputEnergy"),
                [region_column, "Value"],
            ].rename(columns={region_column: "Region"})
        )

    demand_by_island = pd.concat(electricity_demand).groupby("Region")["Value"].sum()
    if set(demand_by_island.index) != {"NI", "SI"} or demand_by_island.le(0).any():
        raise ValueError("Base-year electricity demand must be positive for NI and SI")
    return demand_by_island / demand_by_island.sum()


def create_statistical_difference_parameters(
    electricity_demand_totals: pd.DataFrame,
    baseyear_demand_tables: list[pd.DataFrame],
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
    island_shares = calculate_island_electricity_shares(baseyear_demand_tables)
    output = pd.DataFrame([output.iloc[0] * share for share in island_shares])
    output.insert(0, "Region", ["NI", "SI"])
    output.insert(1, "Comm-IN", "ELC")
    output.insert(1, "TechName", "StatDiffDemand_ELC")
    output["ACT_BND~FX~0"] = 5
    return output
