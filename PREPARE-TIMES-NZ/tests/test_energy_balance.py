"""Unit tests for machine-readable Energy Balance helpers."""

import pandas as pd
import pytest
from prepare_times_nz.utilities.energy_balance import (
    get_balance_value,
    select_gross_pj,
)


def test_select_gross_pj_and_get_balance_value():
    """Balance lookups select the requested year and heating-value basis."""
    data = pd.DataFrame(
        {
            "Entry": ["Transport", "Transport", "Transport"],
            "Fuel": ["Diesel", "Diesel", "Petrol"],
            "Year": [2023, 2023, 2024],
            "Unit": ["Gross PJ", "Net PJ", "Gross PJ"],
            "Value": [106.0, 99.0, 85.0],
        }
    )

    balance = select_gross_pj(data, 2023)

    assert get_balance_value(balance, "Transport", "Diesel") == 106.0
    with pytest.raises(ValueError, match="found 0"):
        get_balance_value(balance, "Transport", "Petrol")
