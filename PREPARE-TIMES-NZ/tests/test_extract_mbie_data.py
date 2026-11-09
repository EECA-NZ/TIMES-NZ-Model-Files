"""Unit tests for MBIE stage-1 extraction helpers."""

import importlib.util
from pathlib import Path

import pandas as pd
import pytest


def load_extract_mbie_data():
    """Load the extraction script without reading source files."""
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts/stage_1_prep_raw_data/extract_mbie_data.py"
    )
    spec = importlib.util.spec_from_file_location("extract_mbie_data", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_select_gas_balance_category_uses_label_not_row_position():
    """A label selects the intended row even when its table position moves."""
    module = load_extract_mbie_data()
    data = pd.DataFrame(
        {
            "Calendar year": ["Transport", "Non-Energy Use1", "Residential"],
            "2025": [1.0, 2.0, 3.0],
        }
    )

    selected = module._select_gas_balance_category(data, "Non-Energy Use")

    assert selected["2025"].tolist() == [2.0]
    with pytest.raises(ValueError, match="found 0"):
        module._select_gas_balance_category(data, "Missing category")


def test_extract_annual_mbie_table_uses_labels_not_column_positions():
    """Annual electricity tables may contain blank spacer and subtotal columns."""
    module = load_extract_mbie_data()
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

    result = module._extract_annual_mbie_table(
        data, "test generation", {"Hydro": "Hydro", "Gas": "Gas"}
    )

    assert result.to_dict("records") == [
        {"Year": 2023, "Hydro": 100.0, "Gas": 20.0},
        {"Year": 2024, "Hydro": 110.0, "Gas": 25.0},
    ]
