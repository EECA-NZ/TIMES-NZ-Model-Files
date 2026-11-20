"""Shared island transformations using synthetic data."""

import pandas as pd
import pytest

from prepare_times_nz.stage_2.common.disaggregate_regions import (
    calculate_generic_regional_splits,
    create_fuel_sector_checks,
    tidy_long_island,
)


@pytest.mark.parametrize("has_override", [False, True])
def test_tidy_long_island(has_override):
    """Preserve values, units, ordering and NaNs; remove zeros and helpers."""
    source = pd.DataFrame(
        {
            "Value": [10.0, 20.0, 0.0, float("nan")],
            "Unit": ["PJ"] * 4,
            "Fuel": ["Gas", "Wood", "Coal", "Other"],
            "Sector": ["Example"] * 4,
            "NIShareSector": [1.0, 0.25, 0.5, float("nan")],
            "NIShare": [1.0, 0.25, 0.5, float("nan")],
            "NI": [10.0, 5.0, 0.0, float("nan")],
            "SI": [0.0, 15.0, 0.0, float("nan")],
            "Extra": ["discard"] * 4,
        }
    )
    if has_override:
        source["NIShareOverride"] = 1.0
    original = source.copy(deep=True)

    result = tidy_long_island(source)

    expected = pd.DataFrame(
        {
            "Sector": ["Example"] * 5,
            "Fuel": ["Gas", "Wood", "Other", "Wood", "Other"],
            "Island": ["NI", "NI", "NI", "SI", "SI"],
            "Unit": ["PJ"] * 5,
            "Value": [10.0, 5.0, float("nan"), 15.0, float("nan")],
        },
        index=[0, 1, 3, 5, 7],
    )
    pd.testing.assert_frame_equal(result, expected)
    pd.testing.assert_frame_equal(source, original)


@pytest.mark.parametrize("islands", [["NI"], ["SI"], ["NI", "SI"]])
def test_create_fuel_sector_checks(islands):
    """Aggregate repeated rows and handle an absent island or zero total."""
    source = pd.DataFrame(
        {
            "Sector": ["Example"] * 4,
            "Fuel": ["Wood", "Wood", "Wood", "Coal"],
            "Island": ["NI", "NI", "SI", "NI"],
            "Value": [2.0, 3.0, 15.0, 0.0],
        }
    )
    source = source[source["Island"].isin(islands)]
    original = source.copy(deep=True)

    result = create_fuel_sector_checks(source)

    expected_wood_share = 0.25 if len(islands) == 2 else float(islands == ["NI"])
    expected_shares = {"Wood": expected_wood_share}
    if "NI" in islands:
        expected_shares["Coal"] = 0.0
    assert result.set_index("Fuel")["NI_Share"].to_dict() == expected_shares
    assert result["Sector"].eq("Example").all()
    pd.testing.assert_frame_equal(source, original)


def test_tidy_long_island_requires_both_island_columns():
    """Keep the existing melt validation rather than silently losing an island."""
    with pytest.raises(KeyError):
        tidy_long_island(pd.DataFrame({"NI": [10.0]}))


def test_calculate_generic_regional_splits_layered_defaults():
    """Use exact, fuel-only, technology-only and sector defaults in that order."""
    source = pd.DataFrame(
        {
            "Sector": ["Example"] * 4,
            "Fuel": ["Gas", "Gas", "Wood", "Wood"],
            "Technology": ["Boiler", "Heater", "Boiler", "Heater"],
            "Unit": ["PJ"] * 4,
            "Value": [10.0] * 4,
        }
    )
    splits = pd.DataFrame(
        {
            "Sector": [" Example "] * 4,
            "Fuel": ["Gas", "Gas", None, None],
            "Technology": ["Boiler", None, "Boiler", None],
            "NI_Share": [1.0, 0.8, 0.6, 0.4],
        }
    )
    original_source, original_splits = source.copy(), splits.copy()

    result = calculate_generic_regional_splits(source, splits)

    assert result.loc[result["Island"] == "NI", "Value"].tolist() == [10, 8, 6, 4]
    assert result.loc[result["Island"] == "SI", "Value"].tolist() == [2, 4, 6]
    assert result["Unit"].eq("PJ").all()
    assert result["Value"].sum() == 40
    pd.testing.assert_frame_equal(source, original_source)
    pd.testing.assert_frame_equal(splits, original_splits)


@pytest.mark.parametrize("sector_override", [False, True])
def test_calculate_generic_regional_splits_fuel_overrides(sector_override):
    """Overrides take precedence; unmatched fuels keep their sector default."""
    source = pd.DataFrame(
        {
            "Sector": ["Example", "Other", "Example"],
            "Fuel": ["Gas", "Gas", "Wood"],
            "Unit": ["PJ"] * 3,
            "Value": [10.0] * 3,
        }
    )
    splits = pd.DataFrame({"Sector": ["Example", "Other"], "NI_Share": [0.25, 0.5]})
    overrides = pd.DataFrame({"Fuel": ["Gas"], "NI_Share": [1.0]})
    if sector_override:
        overrides["Sector"] = "Example"
    originals = [frame.copy() for frame in [source, splits, overrides]]

    result = calculate_generic_regional_splits(source, splits, overrides)

    expected_ni = [10, 5 if sector_override else 10, 2.5]
    assert result.loc[result["Island"] == "NI", "Value"].tolist() == expected_ni
    assert result["Value"].sum() == 30
    assert result["Unit"].eq("PJ").all()
    for frame, original in zip([source, splits, overrides], originals):
        pd.testing.assert_frame_equal(frame, original)


def test_calculate_generic_regional_splits_preserves_validation():
    """Missing split columns still raise an explicit error."""
    with pytest.raises(KeyError, match="Splits file missing columns"):
        calculate_generic_regional_splits(pd.DataFrame(), pd.DataFrame())
    with pytest.raises(KeyError, match="Sector splits file missing columns"):
        calculate_generic_regional_splits(
            pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        )
