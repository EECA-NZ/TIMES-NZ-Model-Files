"""Shared assumption transformations using synthetic data."""

from functools import partial

import pandas as pd
import pytest

from prepare_times_nz.stage_2.common.add_tech_assumptions import (
    add_capital_assumptions,
    add_operating_assumptions,
    normalize_assumption_keys,
    tidy_data,
)
from prepare_times_nz.utilities.deflator import deflate_data


def test_normalize_assumption_keys():
    """Clean keys in place, including tables with only one of the join keys."""
    source = pd.DataFrame(
        {"Technology": ["\ufeff Heat\t pump  ", 12], "Life": [20, 30]}
    )
    normalize_assumption_keys(source)
    assert source.to_dict("list") == {
        "Technology": ["Heat pump", "12"],
        "Life": [20, 30],
    }

    fuels = pd.DataFrame({"Fuel": ["\ufeff Natural\n gas "]})
    normalize_assumption_keys(fuels)
    assert fuels["Fuel"].tolist() == ["Natural gas"]

    no_keys = pd.DataFrame({"Life": [20]})
    normalize_assumption_keys(no_keys)
    assert no_keys.to_dict("list") == {"Life": [20]}


@pytest.mark.parametrize("has_existing_value", [False, True])
def test_tidy_data_preserves_values_and_units(has_existing_value):
    """Melt available metrics, retaining identifiers and missing assumptions."""
    source = pd.DataFrame(
        {
            "Technology": ["Boiler"],
            "Life": [20.0],
            "Efficiency": [0.9],
            "CAPEX": [100.0],
            "OPEX": [float("nan")],
            "AFA": [0.5],
            "InputEnergy": [10.0],
            "OutputEnergy": [9.0],
            "Capacity": [0.6],
        }
    )
    if has_existing_value:
        source["Value"] = 10.0
        source["PriceBaseYear"] = 2020

    result = tidy_data(source, 2023)

    expected = pd.DataFrame(
        {
            "Technology": ["Boiler"] * 8,
            "Variable": [
                "Life",
                "Efficiency",
                "CAPEX",
                "OPEX",
                "AFA",
                "InputEnergy",
                "OutputEnergy",
                "Capacity",
            ],
            "Value": [20.0, 0.9, 100.0, float("nan"), 0.5, 10.0, 9.0, 0.6],
            "Unit": [
                "Years",
                "%",
                "2023 NZD/kW",
                "2023 NZD/kW/year",
                "%",
                "PJ",
                "PJ",
                "GW",
            ],
        }
    )
    pd.testing.assert_frame_equal(result, expected)


def test_tidy_data_rejects_missing_metrics():
    """Keep the existing validation when assumption joins supply no metrics."""
    with pytest.raises(ValueError, match="No columns to melt"):
        tidy_data(pd.DataFrame({"Technology": ["Boiler"]}), 2023)


@pytest.mark.parametrize("sector_afa", [False, True])
@pytest.mark.parametrize("combined_costs", [False, True])
def test_shared_assumption_phases(monkeypatch, sector_afa, combined_costs):
    """Both AFA schemas retain joins, deflation, adjustments, and energy totals."""
    cpi = pd.DataFrame({"Year": [2020, 2023], "CPI_Index": [100.0, 125.0]})
    monkeypatch.setattr(
        "prepare_times_nz.stage_2.common.add_tech_assumptions.deflate_data",
        partial(deflate_data, index_data=cpi),
    )
    source = pd.DataFrame(
        {
            "Technology": ["\ufeff Boiler  Systems "],
            "Fuel": [" Natural\tgas "],
            "Sector": ["Education"],
            "EndUse": ["Heating"],
            "Value": [10.0],
        }
    )
    original = source.copy(deep=True)
    efficiency = pd.DataFrame(
        {"Technology": ["Boiler Systems"], "Fuel": ["Natural gas"], "Efficiency": [0.9]}
    )
    lifetime = pd.DataFrame({"Technology": [" Boiler Systems "], "Life": [20]})
    capex = pd.DataFrame(
        {
            "Technology": ["Boiler Systems"],
            "Fuel": [" Natural gas "],
            "PriceBaseYear": [2020],
            "CAPEX": [100.0],
        }
    )
    opex = capex.rename(columns={"CAPEX": "OPEX"})
    if combined_costs:
        capex["OPEX"] = opex["OPEX"]
        opex = capex
    afa = pd.DataFrame({"Technology": [" Boiler Systems "], "AFA": [0.5]})
    if sector_afa:
        afa["Sector"] = "Education"
        afa["EndUse"] = "Heating"

    result = add_capital_assumptions(source, efficiency, lifetime, capex)
    result["CAPEX"] *= 5  # Commercial adjustments stay between the shared phases.
    result = add_operating_assumptions(result, opex, afa, 2023)

    pd.testing.assert_frame_equal(source, original)
    assert len(result) == 8
    assert result["Technology"].eq("Boiler Systems").all()
    assert result["Fuel"].eq("Natural gas").all()
    values = result.set_index("Variable")["Value"]
    assert values.to_dict() == pytest.approx(
        {
            "Life": 20,
            "Efficiency": 0.9,
            "CAPEX": 625,
            "OPEX": 125,
            "AFA": 0.5,
            "InputEnergy": 10,
            "OutputEnergy": 9,
            "Capacity": 9 / 31.536 / 0.5,
        }
    )
