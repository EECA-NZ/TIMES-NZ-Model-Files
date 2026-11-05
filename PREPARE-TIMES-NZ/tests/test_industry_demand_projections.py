"""Tests for industrial GIC demand projections."""

import pandas as pd
from prepare_times_nz.stage_3.demand_projections import industry


def test_ballance_gic_indices_lock_history_and_close_after_2027():
    """Ballance uses observed GIC demand, then holds 2025 until closure."""
    assumptions = pd.DataFrame(
        {
            "SectorGroup": ["Industry"],
            "Sector": ["Urea"],
            "Method": ["Ballance GIC"],
        }
    )
    gic_data = pd.DataFrame(
        {
            "Participant": ["Ballance", "Ballance", "Ballance"],
            "Date": ["2023-01-01", "2024-01-01", "2025-01-01"],
            "Value": [1000, 800, 1200],
        }
    )

    result = industry.get_gic_growth_indices(assumptions, gic_data, "Ballance GIC")
    indices = result.pivot(index="Year", columns="Scenario", values="Index")

    assert indices.loc[2023].to_dict() == {"Shift": 1.0, "Steady": 1.0}
    assert indices.loc[2024].to_dict() == {"Shift": 0.8, "Steady": 0.8}
    assert indices.loc[2025].to_dict() == {"Shift": 1.2, "Steady": 1.2}
    assert indices.loc[2026].to_dict() == {"Shift": 1.2, "Steady": 1.2}
    assert indices.loc[2027].to_dict() == {"Shift": 1.2, "Steady": 1.2}
    assert indices.loc[2028].to_dict() == {"Shift": 0.0, "Steady": 0.0}
