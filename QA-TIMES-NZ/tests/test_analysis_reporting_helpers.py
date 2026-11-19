"""Sensitivity reporting tests using synthetic objective values."""

import pandas as pd
import pytest

from qa_times_nz.analysis.analysis_reporting_helpers import (
    build_objective_summary_table,
    get_objective_lookup,
)


def test_objective_summary_preserves_order_and_formats_values():
    """Configured rows keep their order, with blank cells for missing values."""
    objectives = {"steady": 1234.5678, "shift": float("nan"), "noets": -2.5}

    result = build_objective_summary_table(
        objectives,
        [("No ETS", "noets", "steady"), ("Base", "steady", "shift")],
    )

    assert result == (
        "| Sensitivity | Steady (NZDb) | Shift (NZDb) |\n"
        "| --- | --- | --- |\n"
        "| No ETS | -2.500 | 1,234.568 |\n"
        "| Base | 1,234.568 |  |"
    )


def test_objective_summary_rejects_missing_scenarios():
    """An absent scenario still raises the existing descriptive error."""
    with pytest.raises(ValueError, match="Missing objective function value for shift"):
        build_objective_summary_table({"steady": 1.0}, [("Base", "steady", "shift")])


def test_objective_lookup_filters_scenarios_and_rejects_duplicates():
    """Only selected scenarios are subject to the one-value validation."""
    source = pd.DataFrame(
        {"Scenario": ["steady", "shift", "shift"], "Value": [1.0, 2.0, 3.0]}
    )

    assert get_objective_lookup(source, {"steady": "Steady"}) == {"steady": 1.0}
    with pytest.raises(
        ValueError, match="Expected one objective function value per scenario: shift"
    ):
        get_objective_lookup(source, {"shift": "Shift"})
