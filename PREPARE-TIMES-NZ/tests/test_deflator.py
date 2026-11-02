"""Unit tests for price-index deflation without Stage-1 files."""

import pandas as pd
from prepare_times_nz.utilities.deflator import deflate_data, deflate_value


def test_deflate_value_uses_an_injected_price_index() -> None:
    """A synthetic CPI table is sufficient for an individual conversion."""
    cpi = pd.DataFrame({"Year": [2018, 2023], "CPI_Index": [100.0, 125.0]})

    result = deflate_value(2018, 2023, 40.0, index_data=cpi)

    assert result == 50.0


def test_deflate_value_noop_does_not_need_a_price_index() -> None:
    """An already-base-year value should not require generated Stage-1 data."""
    assert deflate_value(2023, 2023, 40.0) == 40.0


def test_deflate_data_uses_an_injected_price_index() -> None:
    """Batch deflation does not require generated CPI data in unit tests."""
    cpi = pd.DataFrame({"Year": [2018, 2023], "CPI_Index": [100.0, 125.0]})
    source = pd.DataFrame({"PriceBaseYear": [2018], "INVCOST": [40.0]})

    result = deflate_data(source, 2023, ["INVCOST"], index_data=cpi)

    assert result.to_dict("records") == [{"PriceBaseYear": 2023, "INVCOST": 50.0}]
