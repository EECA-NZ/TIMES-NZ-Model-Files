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
