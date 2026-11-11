"""Unit tests for pure MBIE stage-1 transformations."""

import pandas as pd
import pytest
from prepare_times_nz.stage_1.mbie import (
    extract_annual_table,
    extract_unallocated_onsite_generation,
    select_gas_balance_category,
    tidy_annual_electricity,
    tidy_contingent_reserves,
    tidy_energy_balance,
    tidy_gas_balance_category,
    tidy_generation_capacity,
    tidy_production_profile,
)


def test_select_gas_balance_category_uses_label_not_row_position():
    """A label selects the intended row even when its table position moves."""
    data = pd.DataFrame(
        {
            "Calendar year": ["Transport", "Non-Energy Use1", "Residential"],
            "2025": [1.0, 2.0, 3.0],
        }
    )

    selected = select_gas_balance_category(data, "Non-Energy Use")

    assert selected["2025"].tolist() == [2.0]
    with pytest.raises(ValueError, match="found 0"):
        select_gas_balance_category(data, "Missing category")


def test_extract_annual_mbie_table_uses_labels_not_column_positions():
    """Annual electricity tables may contain blank spacer and subtotal columns."""
    data = pd.DataFrame(
        [
            ["title", None, None, None, None],
            ["Calendar Year", None, "Electricity Only Plants", None, None],
            [None, None, "Hydro", "Gas", "Sub-total"],
            [None, None, None, None, None],
            [2023, None, 100.0, 20.0, 120.0],
            [2024, None, 110.0, 25.0, 135.0],
        ]
    )

    result = extract_annual_table(
        data, "test generation", {"Hydro": "Hydro", "Gas": "Gas"}
    )

    assert result.to_dict("records") == [
        {"Year": 2023, "Hydro": 100.0, "Gas": 20.0},
        {"Year": 2024, "Hydro": 110.0, "Gas": 25.0},
    ]


def test_extract_unallocated_onsite_generation_reads_matching_rows():
    """Matching actual and estimated-sales rows yield one annual PJ series."""
    data = pd.DataFrame(
        [
            [None, None, None, None],
            ["Calendar year", 2022, 2023, 2025],
            ["Unallocated Onsite Generation", 3.0, 4.0, 5.0],
            ["Unallocated Onsite Generation", 3.0, 4.0, 5.0],
        ]
    )

    result = extract_unallocated_onsite_generation(data)

    assert result.to_dict("records") == [
        {"Year": 2022, "Value": 3.0, "Unit": "PJ"},
        {"Year": 2023, "Value": 4.0, "Unit": "PJ"},
        {"Year": 2025, "Value": 5.0, "Unit": "PJ"},
    ]


def test_tidy_energy_balance_uses_a_stable_output_schema():
    """The machine-readable table is standardised without file access."""
    data = pd.DataFrame(
        {
            "entry": ["Unallocated"],
            "fuel": ["Electricity"],
            "year": [2025],
            "unit": ["Gross PJ"],
            "value": [7.0],
        }
    )

    result = tidy_energy_balance(data)

    assert result.to_dict("records") == [
        {
            "Entry": "Unallocated",
            "Fuel": "Electricity",
            "Year": 2025,
            "Unit": "Gross PJ",
            "Value": 7.0,
        }
    ]


def test_tidy_annual_electricity_and_gas_balance_keep_source_values():
    """Workbook tables are reshaped after the script has read them."""
    electricity = pd.DataFrame(
        {
            "Calendar year": ["Hydro1", "Gas"],
            "Annual % change": [0.0, 0.0],
            2023: [10.0, 2.0],
        }
    )
    gas = pd.DataFrame({"Calendar year": ["Non-Energy Use1"], "2023": [3.0]})

    annual = tidy_annual_electricity(
        electricity, slice(0, 2), "Fuel", "GWh", "Annual net electricity generation"
    )
    non_energy = tidy_gas_balance_category(
        gas, "Non-Energy Use", "Balance category", "PJ", "Natural gas non-energy use"
    )

    assert annual[["FuelType", "Year", "Value"]].to_dict("records") == [
        {"FuelType": "Hydro", "Year": 2023, "Value": 10.0},
        {"FuelType": "Gas", "Year": 2023, "Value": 2.0},
    ]
    assert non_energy[["Balance category", "Year", "Value"]].to_dict("records") == [
        {"Balance category": "Non-Energy Use", "Year": "2023", "Value": 3.0}
    ]


def test_tidy_generation_capacity_converts_missing_values_to_numeric_zero():
    """Capacity values must be numeric before missing entries become zero."""
    labels = [
        "Hydro",
        "Geothermal",
        "Biogas",
        "Wind",
        "Solar PV",
        "Diesel",
        "Coal/Gas",
        "Gas",
        "Other Thermal2",
        "Gas3",
        "Other4",
    ]
    raw = pd.DataFrame(
        [
            ["Calendar Year", *([None] * len(labels))],
            [None, *labels],
            [2023, *([1] * 10), None],
        ]
    )

    result = tidy_generation_capacity(raw)

    assert result.loc[result["Technology"] == "Other Cogen", "Value"].item() == 0
    assert pd.api.types.is_numeric_dtype(result["Value"])


def test_tidy_reserves_tables_keep_units_explicit():
    """Production and contingent-reserve transforms are independent of Excel I/O."""
    profile = tidy_production_profile(
        pd.DataFrame({"Field": ["A"], 2025: [None]}), "Gas"
    )
    contingent = tidy_contingent_reserves(pd.DataFrame([["A", 1.0, 2.0, 3.0, 4.0]]))

    assert profile.to_dict("records") == [
        {"Field": "A", "Year": 2025, "Value": 0.0, "Unit": "PJ", "Variable": "Gas"}
    ]
    assert contingent["Unit"].tolist() == [
        "Million Barrels",
        "Million Barrels",
        "kt",
        "PJ",
    ]
