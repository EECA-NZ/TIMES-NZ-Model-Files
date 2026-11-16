"""Tests for residential space-heating allocation helpers."""

import pandas as pd
from prepare_times_nz.stage_2.residential.space_heating_model import (
    add_gshp_allocation_shares,
)


def test_gshp_demand_uses_generic_heat_pump_allocation_shares():
    """GSHP keeps its fuel and technology while reusing heat-pump geography."""
    model_shares = pd.DataFrame(
        {
            "Area": ["Northland", "Canterbury"],
            "DwellingType": ["Detached", "Joined"],
            "Technology": ["Heat Pump (for Heating)"] * 2,
            "Fuel": ["Electricity"] * 2,
            "FuelDemandShare": [0.7, 0.3],
        }
    )
    sh_eeud = pd.DataFrame(
        {
            "Technology": ["Ground source heat pump"],
            "Fuel": ["Geothermal"],
        }
    )

    result = add_gshp_allocation_shares(model_shares, sh_eeud)
    gshp = result[result["Technology"].eq("Ground source heat pump")]

    assert gshp["Fuel"].tolist() == ["Geothermal", "Geothermal"]
    assert gshp["FuelDemandShare"].tolist() == [0.7, 0.3]
