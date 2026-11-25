"""Synthetic checks for shared EEUD alignment text cleaning."""

import pandas as pd
import pytest

from prepare_times_nz.stage_2.common.align_eeud_sectors import (
    GROUP_COLS,
    _norm_header,
    add_times_categories,
    aggregate_eeud,
    is_missing_series,
)
from prepare_times_nz.utilities.data_cleaning import rename_eeud_techs
from prepare_times_nz.utilities.filepaths import ASSUMPTIONS


@pytest.mark.parametrize(
    "header, expected",
    [
        ("\ufeff  Technology-Group_ Name\t", "technology group name"),
        ("FuelGroup", "fuelgroup"),
        (" \t ", ""),
    ],
)
def test_norm_header(header, expected):
    """Keep the exact existing header normalization rules."""
    assert _norm_header(header) == expected


def test_is_missing_series():
    """Handle nulls, token spelling and whitespace without changing the input."""
    source = pd.Series(
        [
            None,
            pd.NA,
            float("nan"),
            "",
            " NA ",
            "n/a",
            "none",
            "NULL",
            "unknown",
            "Gas",
            "nan",
            0,
        ],
        index=range(10, 22),
    )
    original = source.copy(deep=True)

    result = is_missing_series(source)

    expected = pd.Series([True] * 9 + [False] * 3, index=source.index)
    pd.testing.assert_series_equal(result, expected)
    pd.testing.assert_series_equal(source, original)


def test_category_mapping_and_aggregation():
    """Keep unmapped sectors, include missing categories and sum repeated rows."""
    source = pd.DataFrame({column: ["Example"] * 3 for column in GROUP_COLS})
    source["Sector"] = ["Raw sector", "Raw sector", "Unmapped sector"]
    source["Technology"] = None
    source["Year"] = 2023
    source["Unit"] = "PJ"
    source["Value"] = [1.0, 2.0, 4.0]
    mapping = pd.DataFrame({"EEUD": ["Raw sector"], "TIMES": ["Mapped sector"]})

    result = aggregate_eeud(add_times_categories(source, mapping))

    assert result.set_index("Sector")["Value"].to_dict() == {
        "Mapped sector": 3.0,
        "Unmapped sector": 4.0,
    }
    assert result["Technology"].eq("NA").all()
    assert result["Unit"].eq("PJ").all()
    assert "TIMES_Sector" not in result.columns


def test_residential_solar_rename_rule_only_touches_matching_rows():
    """Solar cylinders are relabelled; electric cylinders keep their name."""
    df = pd.DataFrame(
        {
            "SectorGroup": ["Residential", "Residential", "Commercial"],
            "Sector": ["Residential", "Residential", "Commercial"],
            "Fuel": ["Solar", "Electricity", "Solar"],
            "Technology": ["Hot Water Cylinder"] * 3,
            "EndUse": ["Water Heating"] * 3,
        }
    )
    out = rename_eeud_techs(df, ASSUMPTIONS / "eeud_patches/times_eeud_renames.toml")
    assert out["Technology"].tolist() == [
        "Solar hot water cylinder",
        "Hot Water Cylinder",
        "Hot Water Cylinder",
    ]
