"""Regression tests for generated future agriculture process topology."""

import importlib.util
from pathlib import Path

SCRIPT = (
    Path(__file__).parents[1]
    / "scripts/stage_4_veda_format/create_newtechs_agr_files.py"
)
SPEC = importlib.util.spec_from_file_location("create_newtechs_agr_files", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_future_agriculture_topology_uses_detailed_service_commodities() -> None:
    topology = MODULE.create_newtech_topology()

    expected = {
        "ADCF-MoTP-Mob-Bike-ELC": "ADCF-Bike-MoTP-Mob",
        "AFORE-MoTP-Mob-GB-ELC": "AFORE-GB-MoTP-Mob",
        "AINDC-SH-Boiler-ELC": "AINDC-Boiler-SH",
        "AHORT-MoTP-Stat-Motor-ELC": "AHORT-MoTP-Stat",
    }
    actual = topology.set_index("TechName")["Comm-Out"].to_dict()

    assert len(topology) == 30
    assert {process: actual[process] for process in expected} == expected


def test_horticulture_stationary_motor_is_concordance_backed() -> None:
    definitions = MODULE.create_newtech_process_defintions({})
    motor = definitions.loc[
        definitions["Process"].eq("AHORT-MoTP-Stat-Motor-ELC")
    ].iloc[0]

    assert motor["Technology"] == "Electric Motor"
    assert motor["TechnologyGroup"] == "Stationary Motors"


def test_future_agriculture_processes_do_not_set_primary_commodity_groups() -> None:
    processes = MODULE.create_newtech_process_df(
        {"Columns": ["Sets", "TechName", "Tact", "Tcap", "TsLvl"]}
    )

    assert "PrimaryCG" not in processes.columns


def test_future_agriculture_topology_rejects_unknown_concordance_codes(
    tmp_path,
) -> None:
    config = tmp_path / "bad_topology.toml"
    config.write_text("""[newtechsInvalid]
TechCode = "NotATechnology"
EndUse = "MoTP-Mob"
InputFuel = ["ELC"]
Sectors = ["ADCF"]
""")

    try:
        MODULE.create_newtech_topology(config)
    except ValueError as error:
        assert "Unknown agriculture technology code" in str(error)
    else:
        raise AssertionError("Expected an invalid concordance code to be rejected")
