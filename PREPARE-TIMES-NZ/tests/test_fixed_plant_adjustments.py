"""Tests for fixed plant seasonal adjustment helpers."""

import pandas as pd
import pytest
from prepare_times_nz.stage_4.electricity.fixed_plant_adjustments import (
    extract_season_from_timeslice,
    format_fixed_plant_adjustment_output,
    join_fixed_plants_to_renewable_availability,
    prepare_renewable_availability_for_join,
)


def test_extract_season_from_timeslice_handles_full_and_parent_slices():
    """
    TIMES time slices should map cleanly onto the seasonal join key.
    """

    assert extract_season_from_timeslice("WIN-WK-P") == "WIN"
    assert extract_season_from_timeslice("SPR-") == "SPR"


def test_prepare_renewable_availability_for_join_adds_season_and_drops_year_zero():
    """
    Join prep should ignore interpolation rows and retain concrete curve years.
    """

    renewable = pd.DataFrame(
        {
            "TimeSlice": ["WIN-WK-P", "WIN-WE-N"],
            "LimType": ["UP", "UP"],
            "Attribute": ["NCAP_AF", "NCAP_AF"],
            "NI": [0.6, 0.5],
            "SI": [0.4, 0.3],
            "Pset_PN": ["ELC_HydRR_*", "ELC_HydRR_*"],
            "Year": [0, 2024],
        }
    )

    result = prepare_renewable_availability_for_join(renewable)

    assert result["Season"].tolist() == ["WIN"]
    assert "Year" not in result.columns


def test_join_fixed_plants_to_renewable_availability_matches_on_pset_and_season():
    """
    Fixed-plant season rows should expand to all matching renewable timeslices.
    """

    fixed_plants = pd.DataFrame(
        {
            "TechName": ["Hydro A", "Hydro A", "Hydro B"],
            "TechCode": ["HydRR", "HydRR", "HydRR"],
            "Pset_PN": ["ELC_HydRR_*", "ELC_HydRR_*", "ELC_HydRR_*"],
            "Year": [2030, 2030, 2030],
            "Region": ["NI", "NI", "SI"],
            "Season": ["WIN", "SPR", "WIN"],
            "Share": [1.0, 0.5, 1.0],
        }
    )
    renewable = pd.DataFrame(
        {
            "TimeSlice": ["WIN-WK-P", "WIN-WE-N", "SPR-WK-D", "SPR-"],
            "LimType": ["UP", "UP", "UP", "UP"],
            "Attribute": ["NCAP_AF", "NCAP_AF", "NCAP_AF", "NCAP_AFS"],
            "NI": [0.6, 0.5, 0.7, 0.8],
            "SI": [0.4, 0.3, 0.6, 0.75],
            "Pset_PN": ["ELC_HydRR_*"] * 4,
            "Year": [2024, 2024, 2024, 2024],
        }
    )

    result = join_fixed_plants_to_renewable_availability(fixed_plants, renewable)

    assert result["TimeSlice"].tolist() == [
        "SPR-",
        "SPR-WK-D",
        "WIN-WE-N",
        "WIN-WK-P",
        "WIN-WE-N",
        "WIN-WK-P",
    ]
    assert result["Season"].tolist() == ["SPR", "SPR", "WIN", "WIN", "WIN", "WIN"]
    assert result["Year"].tolist() == [2030, 2030, 2030, 2030, 2030, 2030]
    assert result["NI"].tolist() == [0.8, 0.7, 0.5, 0.6, 0.5, 0.6]
    assert result["SI"].tolist() == [0.75, 0.6, 0.3, 0.4, 0.3, 0.4]


def test_format_fixed_plant_adjustment_output_creates_value_and_drops_helper_columns():
    """
    Downstream formatting should emit a reduced commissioning year and an
    unmodified following year, then trim join-only fields.
    """

    joined = pd.DataFrame(
        {
            "TechName": ["Hydro A", "Hydro B"],
            "TechCode": ["HydRR", "HydRR"],
            "Pset_PN": ["ELC_HydRR_*", "ELC_HydRR_*"],
            "Year": [2030, 2030],
            "Region": ["NI", "SI"],
            "Season": ["WIN", "WIN"],
            "Share": [0.5, 0.25],
            "TimeSlice": ["WIN-WK-P", "WIN-WK-P"],
            "LimType": ["UP", "UP"],
            "Attribute": ["NCAP_AF", "NCAP_AF"],
            "NI": [0.6, 0.6],
            "SI": [0.4, 0.4],
        }
    )

    result = format_fixed_plant_adjustment_output(joined)

    assert result["TechName"].tolist() == ["Hydro A", "Hydro A", "Hydro B", "Hydro B"]
    assert result["Year"].tolist() == [2030, 2031, 2030, 2031]
    assert result["Region"].tolist() == ["NI", "NI", "SI", "SI"]
    assert result["Value"].tolist() == [0.3, 0.6, 0.1, 0.4]
    assert "NI" not in result.columns
    assert "SI" not in result.columns
    assert "Pset_PN" not in result.columns
    assert "TechCode" not in result.columns
    assert "Season" not in result.columns
    assert "Share" not in result.columns


def test_join_fixed_plants_to_renewable_availability_raises_on_missing_match():
    """
    A missing seasonal renewable curve should fail loudly.
    """

    fixed_plants = pd.DataFrame(
        {
            "TechName": ["Solar A"],
            "TechCode": ["SolarTrack"],
            "Pset_PN": ["ELC_SolarTrack_*"],
            "Year": [2030],
            "Region": ["NI"],
            "Season": ["SUM"],
            "Share": [1.0],
        }
    )
    renewable = pd.DataFrame(
        {
            "TimeSlice": ["WIN-WK-P"],
            "LimType": ["FX"],
            "Attribute": ["NCAP_AF"],
            "NI": [0.9],
            "SI": [0.8],
            "Pset_PN": ["ELC_SolarTrack_*"],
            "Year": [2024],
        }
    )

    with pytest.raises(ValueError, match="could not be matched"):
        join_fixed_plants_to_renewable_availability(fixed_plants, renewable)
