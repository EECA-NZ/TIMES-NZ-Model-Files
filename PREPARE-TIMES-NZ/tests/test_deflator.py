"""Unit tests for price-index deflation without Stage-1 files."""

import pandas as pd
import pytest

from prepare_times_nz.utilities.deflator import (
    deflate_columns_rowwise,
    deflate_data,
    deflate_value,
)


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


@pytest.mark.parametrize(
    "method,index_column", [("cpi", "CPI_Index"), ("cgpi", "CGPI_Index")]
)
def test_deflate_columns_rowwise_uses_each_columns_base_year(method, index_column):
    """Both index methods preserve source columns and add deflated NZD columns."""
    index_data = pd.DataFrame(
        {"Year": [2018, 2020, 2023], index_column: [100.0, 125.0, 150.0]}
    )
    source = pd.DataFrame(
        {
            "purchase_year": [2018, 2020],
            "operation_year": [2020, 2018],
            "purchase_cost": [40.0, 50.0],
            "operation_cost": [10.0, 20.0],
        }
    )

    result = deflate_columns_rowwise(
        source,
        {"purchase_cost": "purchase_year", "operation_cost": "operation_year"},
        method=method,
        index_data=index_data,
    )

    assert result["purchase_cost"].tolist() == [40.0, 50.0]
    assert result["operation_cost"].tolist() == [10.0, 20.0]
    assert result["purchase_cost_nzd"].tolist() == [60.0, 60.0]
    assert result["operation_cost_nzd"].tolist() == [12.0, 30.0]
