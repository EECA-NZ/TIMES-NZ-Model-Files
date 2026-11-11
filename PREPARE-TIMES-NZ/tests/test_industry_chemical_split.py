"""Tests for the industrial chemicals demand split."""

import pandas as pd
from prepare_times_nz.stage_2.industry import industry_align_eeud_sectors as chemicals


def test_split_chemicals_out_removes_allocated_generic_chemical_demand(monkeypatch):
    columns = [
        "Year",
        "SectorGroup",
        "Sector",
        "SectorANZSIC",
        "FuelGroup",
        "Fuel",
        "TechnologyGroup",
        "Technology",
        "EnduseGroup",
        "EndUse",
        "Transport",
        "Unit",
        "Value",
    ]
    generic_chemicals = pd.DataFrame(
        [
            [
                2023,
                "Industrial",
                "Petroleum, Basic Chemical and Rubber Product Manufacturing",
                "C17-C19",
                "Fossil Fuel",
                "Natural Gas",
                "Heat/Cooling Devices",
                "Reformer",
                "Heating/Cooling",
                "High Temperature Heat (>300 C), Process Requirements",
                "Non-Transport",
                "PJ",
                10.0,
            ]
        ],
        columns=columns,
    )
    methanol = generic_chemicals.assign(Sector="Methanol", Value=7.0)
    urea = generic_chemicals.assign(Sector="Urea", Value=2.0)
    monkeypatch.setattr(
        chemicals,
        "create_chemical_nga_shares",
        lambda *_: pd.concat([methanol, urea], ignore_index=True),
    )

    result = chemicals.split_chemicals_out(generic_chemicals, None, None, None)

    values = result.groupby("Sector")["Value"].sum().to_dict()
    assert values == {
        "Methanol": 7.0,
        "Petroleum, Basic Chemical and Rubber Product Manufacturing": 1.0,
        "Urea": 2.0,
    }
