"""Unit tests for pure MBIE stage-1 transformations."""

import pandas as pd
import pytest
from prepare_times_nz.stage_1.mbie import (
    extract_annual_table,
    extract_unallocated_onsite_generation,
    select_gas_balance_category,
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
