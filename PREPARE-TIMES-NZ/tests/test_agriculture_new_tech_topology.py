"""Unit tests for future-agriculture topology expansion."""

import importlib.util
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).parents[1]
    / "scripts/stage_4_veda_format/create_newtechs_agr_files.py"
)
SPEC = importlib.util.spec_from_file_location("create_newtechs_agr_files", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_topology_entry_expands_sector_and_fuel_combinations() -> None:
    entry = {
        "TechCode": "Bike",
        "EndUse": "MoTP-Mob",
        "InputFuel": ["ELC", "H2R"],
        "Sectors": ["ADCF"],
        "CommodityOutTemplate": "{sector}-{technology}-{end_use}",
    }

    result = MODULE._expand_topology_entry(
        "newtechsBikes",
        entry,
        {"ADCF": "Dairy farming"},
        {"MoTP-Mob"},
        {("Dairy farming", "Bike")},
    )

    assert result == [
        {
            "TechName": "ADCF-MoTP-Mob-Bike-ELC",
            "Comm-In": "AGRELC",
            "Comm-Out": "ADCF-Bike-MoTP-Mob",
            "Sector_TIMES": "ADCF",
            "EndUse_TIMES": "MoTP-Mob",
            "Technology_TIMES": "Bike",
        },
        {
            "TechName": "ADCF-MoTP-Mob-Bike-H2R",
            "Comm-In": "AGRH2R",
            "Comm-Out": "ADCF-Bike-MoTP-Mob",
            "Sector_TIMES": "ADCF",
            "EndUse_TIMES": "MoTP-Mob",
            "Technology_TIMES": "Bike",
        },
    ]


def test_topology_entry_rejects_unknown_concordance_code() -> None:
    entry = {
        "TechCode": "NotATechnology",
        "EndUse": "MoTP-Mob",
        "InputFuel": ["ELC"],
        "Sectors": ["ADCF"],
    }

    with pytest.raises(ValueError, match="Unknown agriculture technology code"):
        MODULE._expand_topology_entry(
            "newtechsInvalid",
            entry,
            {"ADCF": "Dairy farming"},
            {"MoTP-Mob"},
            {("Dairy farming", "Bike")},
        )
