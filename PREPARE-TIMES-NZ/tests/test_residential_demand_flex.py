"""Tests for residential demand flexibility topology helpers."""

import pandas as pd
import pytest
from prepare_times_nz.stage_4.baseyear.residential import (
    add_demand_flex_intermediate_outputs,
    get_commodity_demand,
    get_demand_flex_topology,
    get_intermediate_commodity_name,
    get_model_switch,
    parse_switch_value,
)


def test_get_intermediate_commodity_name_uses_region_and_tech_detail():
    """Intermediate commodity names should retain the useful tech detail."""
    tech_name = "RES-DD-ELC-HWATER_C-WH_LOW"

    assert get_intermediate_commodity_name(tech_name) == "DD-HWATER_C-WH_LOW"


def test_get_intermediate_commodity_name_handles_space_heating_heat_pumps():
    """Residential heat pump space heating should route through HPSH detail."""
    tech_name = "RES-JD-ELC-HPSH-S_HEAT"

    assert get_intermediate_commodity_name(tech_name) == "JD-HPSH-S_HEAT"


def test_demand_flex_topology_keeps_final_demand_on_original_commodity():
    """Flexible demand topology should not move final demand to intermediates."""
    df = pd.DataFrame(
        {
            "TechName": [
                "RES-DD-ELC-HWATER_C-WH_LOW",
                "RES-DD-ELC-HWATER_C-WH_LOW",
                "RES-DD-LPG-HWATER_G-WH_LOW",
            ],
            "Comm-OUT": ["DD-WH_LOW", "DD-WH_LOW", "DD-WH_LOW"],
            "Region": ["NI", "SI", "NI"],
            "ACT_BND": [1.0, 2.0, 3.0],
        }
    )

    topology = get_demand_flex_topology(df, {"RES-DD-ELC-HWATER_C-WH_LOW"})
    rewritten = add_demand_flex_intermediate_outputs(df, topology)
    demand = get_commodity_demand(df)

    assert topology.to_dict("records") == [
        {
            "TechName": "RES-DD-ELC-HWATER_C-WH_LOW",
            "Comm-OUT": "DD-WH_LOW",
            "Comm-IN": "DD-HWATER_C-WH_LOW",
        }
    ]
    assert set(rewritten["Comm-OUT"]) == {"DD-HWATER_C-WH_LOW", "DD-WH_LOW"}
    assert "DD-HWATER_C-WH_LOW" not in set(demand["CommName"])


def test_get_model_switch_reads_enabled_value(tmp_path):
    """User switch CSV should control residential demand-flex intermediates."""
    switch_file = tmp_path / "model_switches.csv"
    switch_file.write_text(
        "Switch,Enabled\nResidentialDemandFlexIntermediates,false\n",
        encoding="utf-8",
    )

    assert not get_model_switch(
        "ResidentialDemandFlexIntermediates", filepath=switch_file
    )


def test_get_model_switch_uses_default_for_missing_file(tmp_path):
    """Missing switch files should preserve the current enabled behaviour."""
    assert get_model_switch(
        "ResidentialDemandFlexIntermediates", filepath=tmp_path / "missing.csv"
    )


def test_parse_switch_value_rejects_unclear_values():
    """Switch values should fail loudly if they are ambiguous."""
    with pytest.raises(ValueError):
        parse_switch_value("maybe")
