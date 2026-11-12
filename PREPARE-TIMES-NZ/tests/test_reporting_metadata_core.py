import pandas as pd
import pytest
from prepare_times_nz.reporting_metadata.core import (
    build_declaration_units,
    build_distribution_processes,
    build_electricity_generation_processes,
    build_energy_commodities,
    build_timeslices,
)


def test_build_energy_commodities_includes_generic_sectoral_and_distribution_codes():
    fuels = pd.DataFrame({"CommodityCode": ["ELC"], "Commodity": ["Electricity"]})
    sectors = pd.DataFrame({"SectorCode": ["IND"], "Sector": ["Industry"]})

    result = build_energy_commodities(fuels, sectors)

    assert set(result["Commodity"]) >= {"ELC", "INDELC", "ELCDD"}
    assert result.loc[result["Commodity"] == "ELC", "Fuel"].item() == "Electricity"


def test_build_distribution_processes_labels_generated_and_declared_rows():
    fuels = pd.DataFrame({"CommodityCode": ["ELC"], "Commodity": ["Electricity"]})
    sectors = pd.DataFrame({"SectorCode": ["IND"], "Sector": ["Industry"]})
    extra = pd.DataFrame(
        {
            "Process": ["G_ELC_HV"],
            "Sector": ["Electricity distribution"],
            "Commodity": ["Electricity"],
            "ProcessGroup": ["Distribution"],
        }
    )

    result = build_distribution_processes(fuels, sectors, extra)

    assert set(result["Process"]) == {"FTE_INDELC", "G_ELC_HV"}


def test_build_declaration_units_forwards_inherited_cells_before_selecting_fields():
    table = pd.DataFrame(
        {
            "TechName": ["A", "B"],
            "Sets": ["DMD", None],
            "TACT": ["PJ", None],
            "TCAP": ["GW", None],
        }
    )

    result = build_declaration_units([table], ["techname", "sets", "tact", "tcap"])

    assert result.to_dict("records") == [
        {"techname": "A", "sets": "DMD", "tact": "PJ", "tcap": "GW"},
        {"techname": "B", "sets": "DMD", "tact": "PJ", "tcap": "GW"},
    ]


def test_build_timeslices_uses_declared_order_clean_labels_and_year_fractions():
    result = build_timeslices(
        {"Season": ["WIN-"], "Weekly": ["WE-", "WK-"], "DayNite": ["N", "P"]},
        pd.DataFrame(
            {
                "TimeSlice": ["WIN-WE-N", "WIN-WE-P", "WIN-WK-N", "WIN-WK-P"],
                "YRFR": [0.1, 0.2, 0.3, 0.4],
            }
        ),
    )

    assert result["TimeSlice"].tolist() == [
        "ANNUAL",
        "WIN-WE-N",
        "WIN-WE-P",
        "WIN-WK-N",
        "WIN-WK-P",
    ]
    assert result.loc[1, "TimeSliceLabel"] == "Winter — Weekend — Night"
    assert result.loc[4, "YearFraction"] == 0.4


def test_build_electricity_generation_processes_rejects_unlabelled_technology():
    base = pd.DataFrame(
        {
            "TechName": ["ELC_UNKNOWN"],
            "PlantName": ["Unknown"],
            "Tech_TIMES": ["Unknown"],
        }
    )
    empty = pd.DataFrame(columns=["TechName", "Plant", "Tech_TIMES"])
    offshore = pd.DataFrame(columns=["TechName", "Region", "Tech_TIMES"])
    labels = pd.DataFrame(
        {"Tech_TIMES": ["HydSC"], "Technology": ["Hydro"], "TechnologyGroup": ["Hydro"]}
    )

    with pytest.raises(ValueError, match="Unknown"):
        build_electricity_generation_processes(base, empty, offshore, labels)
