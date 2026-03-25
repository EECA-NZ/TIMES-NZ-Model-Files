"""Tests for NIWA solar availability-factor helpers."""

import importlib.util
from pathlib import Path

import pandas as pd
import pytest


def load_solar_build_curves():
    """
    Load the script module directly from its path for test usage.
    """
    module_path = (
        Path(__file__).resolve().parents[1]
        / "scripts/stage_3_scenarios/electricity/solar_build_curves.py"
    )
    spec = importlib.util.spec_from_file_location("solar_build_curves", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_aggregate_island_curves_uses_configured_zone_weights():
    """
    Island curves should use configured zone weights within each island.
    """
    module = load_solar_build_curves()
    zone_factors = pd.DataFrame(
        {
            "Tech_TIMES": ["SolarDistSmall"] * 4,
            "ZoneCode": ["AK", "HN", "CC", "DN"],
            "Region": ["Auckland", "Hamilton", "Christchurch", "Dunedin"],
            "TimeSlice": ["SUM-WK-D"] * 4,
            "Island": ["NI", "NI", "SI", "SI"],
            "AvailabilityFactor": [0.2, 0.4, 0.6, 0.8],
            "HoursInTimeSlice": [600, 100, 200, 400],
        }
    )
    zone_weights = pd.DataFrame(
        {
            "ZoneCode": ["AK", "HN", "CC", "DN"],
            "Region": ["Auckland", "Hamilton", "Christchurch", "Dunedin"],
            "Island": ["NI", "NI", "SI", "SI"],
            "Weight": [0.75, 0.25, 0.1, 0.9],
            "IslandWeightTotal": [1.0, 1.0, 1.0, 1.0],
            "NormalizedWeight": [0.75, 0.25, 0.1, 0.9],
        }
    )

    result = module.aggregate_island_curves(zone_factors, zone_weights)

    row = result.to_dict(orient="records")[0]
    assert row["TimeSlice"] == "SUM-WK-D"
    assert row["Tech_TIMES"] == "SolarDistSmall"
    assert row["NI"] == pytest.approx((0.2 * 0.75) + (0.4 * 0.25))
    assert row["SI"] == pytest.approx((0.6 * 0.1) + (0.8 * 0.9))


def test_aggregate_island_curves_requires_weights_for_every_zone():
    """
    Island aggregation should fail if any zone lacks a configured weight.
    """
    module = load_solar_build_curves()
    zone_factors = pd.DataFrame(
        {
            "Tech_TIMES": ["SolarDistBifacial"],
            "ZoneCode": ["AK"],
            "Region": ["Auckland"],
            "TimeSlice": ["SUM-WK-D"],
            "Island": ["NI"],
            "AvailabilityFactor": [0.2],
            "HoursInTimeSlice": [600],
        }
    )
    zone_weights = pd.DataFrame(
        {
            "ZoneCode": ["HN"],
            "Region": ["Hamilton"],
            "Island": ["NI"],
            "Weight": [1.0],
            "IslandWeightTotal": [1.0],
            "NormalizedWeight": [1.0],
        }
    )

    with pytest.raises(ValueError, match="Missing configured solar zone weights"):
        module.aggregate_island_curves(zone_factors, zone_weights)


def test_merge_solar_and_static_curves_replaces_only_solar_rows():
    """
    Generated solar curves should replace only the solar rows in the static table.
    """
    module = load_solar_build_curves()
    solar = pd.DataFrame(
        {
            "TimeSlice": ["SUM-WK-D", "SUM-WK-D"],
            "Tech_TIMES": ["SolarDistSmall", "SolarDistBifacial"],
            "NI": [0.3, 0.35],
            "SI": [0.4, 0.45],
        }
    )
    static = pd.DataFrame(
        {
            "TimeSlice": ["SUM-WK-D", "SUM-WK-D", "SUM-WK-D"],
            "TechCode": ["SolarDistSmall", "SolarDistBifacial", "WindOn"],
            "NI": [0.1, 0.2, 0.5],
            "SI": [0.2, 0.3, 0.5],
        }
    )

    result = module.merge_solar_and_static_curves(solar, static)

    assert result.to_dict(orient="records") == [
        {
            "TimeSlice": "SUM-WK-D",
            "Tech_TIMES": "SolarDistBifacial",
            "NI": 0.35,
            "SI": 0.45,
        },
        {
            "TimeSlice": "SUM-WK-D",
            "Tech_TIMES": "SolarDistSmall",
            "NI": 0.3,
            "SI": 0.4,
        },
        {"TimeSlice": "SUM-WK-D", "Tech_TIMES": "WindOn", "NI": 0.5, "SI": 0.5},
    ]
