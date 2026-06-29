"""Tests for residential demand flexibility topology helpers."""

import pandas as pd
from prepare_times_nz.stage_4.baseyear.residential import (
    add_demand_flex_intermediate_outputs,
    get_commodity_demand,
    get_demand_flex_topology,
    get_intermediate_commodity_name,
)


def test_get_intermediate_commodity_name_uses_region_and_tech_detail():
    """Intermediate commodity names should retain the useful tech detail."""
    tech_name = "RES-DD-ELC-HWATER_C-WH_LOW"

    assert get_intermediate_commodity_name(tech_name) == "DD-HWATER_C-WH_LOW"


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
