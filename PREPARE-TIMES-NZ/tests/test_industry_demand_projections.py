"""Tests for industrial GIC demand projections."""

import pandas as pd

from prepare_times_nz.stage_3.demand_projections import industry


def test_ballance_gic_indices_use_the_provisional_2026_estimate():
    """The provisional estimate overrides observed 2026 demand until closure."""
    assumptions = pd.DataFrame(
        {
            "SectorGroup": ["Industry"],
            "Sector": ["Urea"],
            "Method": ["Ballance GIC"],
        }
    )
    gic_data = pd.DataFrame(
        {
            "Participant": ["Ballance", "Ballance", "Ballance", "Ballance"],
            "Date": ["2023-01-01", "2024-01-01", "2025-01-01", "2026-01-01"],
            "Value": [1000, 800, 1200, 6000],
        }
    )
    annual_estimates = pd.DataFrame(
        {
            "Method": ["Ballance GIC"],
            "Year": [2026],
            "Value": [1.1],
            "Unit": ["PJ"],
        }
    )

    result = industry.get_gic_growth_indices(
        assumptions, gic_data, annual_estimates, "Ballance GIC"
    )
    indices = result.pivot(index="Year", columns="Scenario", values="Index")

    assert indices.loc[2023].to_dict() == {"Shift": 1.0, "Steady": 1.0}
    assert indices.loc[2024].to_dict() == {"Shift": 0.8, "Steady": 0.8}
    assert indices.loc[2025].to_dict() == {"Shift": 1.2, "Steady": 1.2}
    assert indices.loc[2026].to_dict() == {"Shift": 1.1, "Steady": 1.1}
    assert indices.loc[2027].to_dict() == {"Shift": 1.1, "Steady": 1.1}
    assert indices.loc[2028].to_dict() == {"Shift": 0.0, "Steady": 0.0}


def test_methanex_gic_indices_sum_participants_and_expand_each_sector():
    """Both sectors carry the last observed index through the closure year."""
    assumptions = pd.DataFrame(
        {
            "SectorGroup": ["Industry", "Industry"],
            "Sector": ["Methanol", "Other methanol"],
            "Method": ["Methanex GIC", "Methanex GIC"],
        }
    )
    gic_data = pd.DataFrame(
        {
            "Participant": industry.METHANEX_PARTICIPANTS * 3,
            "Date": ["2023-01-01"] * 2 + ["2024-01-01"] * 2 + ["2025-01-01"] * 2,
            "Value": [600, 400, 300, 200, 120, 80],
        }
    )
    annual_estimates = pd.DataFrame(columns=["Method", "Year", "Value", "Unit"])

    result = industry.get_gic_growth_indices(
        assumptions, gic_data, annual_estimates, "Methanex GIC"
    )

    assert not result.duplicated(["Sector", "Year", "Scenario"]).any()
    indices = result.pivot(index=["Sector", "Scenario"], columns="Year", values="Index")
    assert len(indices) == 4
    assert indices[2023].eq(1.0).all()
    assert indices[2024].eq(0.5).all()
    assert indices[2025].eq(0.2).all()
    assert indices[2026].eq(0.2).all()
    assert indices[2027].eq(0.0).all()
