"""
doit build file for PREPARE-TIMES-NZ
====================================

This is the build recipe (doit) for PREPARE-TIMES-NZ. It orchestrates raw data
extraction -> baseyear calibration -> scenario growth -> VEDA artefacts.

Expected directories (under DATA_INTERMEDIATE):
  - stage_0_config/
  - stage_1_input_data/
  - stage_2_baseyear_data/
  - stage_3_scenario_data/
  - stage_4_veda_format/

Run:
    doit            # execute everything required for the VEDA workbooks
    doit list       # list all defined tasks
    doit clean      # remove generated artefacts

Pipeline stages
--------------
* Stage-0: TOML -> explicit 'stage_0_config/'
* Stage-1: raw extractions -> 'stage_1_input_data/'
* Stage-2: base-year calculations -> 'stage_2_baseyear_data/'
* Stage-3: scenario growth assumptions -> 'stage_3_scenario_data/'
* Stage-4: VEDA-ready CSVs + final Excel workbooks -> 'stage_4_veda_format/', 'output/'

Each task lists real CSV/parquet artefacts as 'targets' so *doit* re-runs a
step only when:
  * any of its inputs (scripts, upstream data) changed, or
  * its outputs are missing / deleted.

Note:

* The script globs contents of folders like `data_intermediate`. Keep these clean and
run `doit` twice to ensure that all output data is picked up.

* Not all output files are listed for each script - only key / sentinel outputs.

"""

import sys
from os import PathLike
from pathlib import Path
from typing import Iterator

from prepare_times_nz.utilities.filepaths import (
    ASSUMPTIONS,
    CONCORDANCES,
    DATA_INTERMEDIATE,
    DATA_RAW,
    OUTPUT_LOCATION,
    STAGE_0_SCRIPTS,
    STAGE_1_SCRIPTS,
    STAGE_2_SCRIPTS,
    STAGE_3_SCRIPTS,
    STAGE_4_SCRIPTS,
)

##########################################
# Constants

# Running 'doit' runs the full chain.
DOIT_CONFIG = {
    "verbosity": 2,
    "dep_file": ".cache/doit/db",
    "default_tasks": ["stage_5_build_excel"],
}

# Pattern to identify datasets
GLOB_PATTERN = "*.*"

# Intermediate data directories
S0_DIR = "stage_0_config"
S1_DIR = "stage_1_input_data"
S2_DIR = "stage_2_baseyear_data"
S3_DIR = "stage_3_scenario_data"
S4_DIR = "stage_4_veda_format"

# Active interpreter
PY = sys.executable

# Stage-0: TOML -> config_metadata.csv
CONFIG_DIR = DATA_INTERMEDIATE / S0_DIR
CONFIG_META_CSV = CONFIG_DIR / "config_metadata.csv"


##########################################
# Helpers


def _run(script: str) -> str:
    """Return a shell command that invokes *script* with the current Python.

    We generate a string instead of a list so that *doit* passes it straight to
    the shell, which keeps quoting simple and honours the active virtual-env.
    """
    return f'"{PY}" "{script}"'


def _intermediate_out(rel_path: str, *sub):
    """
    Convenience helper to construct an absolute path to an output file
    """
    return Path(DATA_INTERMEDIATE, *sub, rel_path)


def _out(rel_path: str) -> Path:
    """Absolute path for a workbook under OUTPUT_LOCATION"""
    return OUTPUT_LOCATION / rel_path


def _files_in_path(path: str | PathLike, pattern: str = GLOB_PATTERN) -> list[Path]:
    """
    Recursively list *all* files inside the given path

    Parameters
    ----------
    path : str | PathLike
        root path. Broader applicability than _files_in_stage


    Returns
    -------
    list[Path]
        Absolute ``Path`` objects for every file found.
    """
    return [p for p in path.rglob(pattern) if p.is_file()]


def _files_in_stage(
    stage_dir: str | PathLike, pattern: str = GLOB_PATTERN
) -> list[Path]:
    """
    Recursively list *all* files inside the given staging directory.

    Parameters
    ----------
    stage_dir : str | PathLike
        Directory name relative to DATA_INTERMEDIATE - e.g. S2_DIR

    Returns
    -------
    list[Path]
        Absolute ``Path`` objects for every file found.
    """
    root = DATA_INTERMEDIATE / stage_dir
    return _files_in_path(root, pattern=pattern)


##########################################
# Dependency Definitions
##########################################


# Stage-0 inputs:
STAGE_0_INPUTS = _files_in_path((DATA_RAW / "user_config"))
ASSUMPTION_INPUTS = _files_in_path(ASSUMPTIONS)
CONCORDANCE_INPUTS = _files_in_path(CONCORDANCES)


# Raw data input to stage 1

STAGE_1_INPUTS: dict[str, list[Path]] = {
    "extract_ea_data": _files_in_path(DATA_RAW / "external_data/electricity_authority"),
    "extract_eeud": _files_in_path(DATA_RAW / "eeca_data/eeud"),
    "extract_gic_data": _files_in_path(DATA_RAW / "external_data/gic"),
    "extract_mbie_data": _files_in_path(DATA_RAW / "external_data/mbie"),
    "extract_nrel_data": _files_in_path(DATA_RAW / "external_data/nrel"),
    "extract_snz_data": _files_in_path(DATA_RAW / "external_data/statsnz"),
    # Transport inputs
    "extract_fleet_vkt_pj_data": _files_in_path(DATA_RAW / "eeca_data/eeud")
    + _files_in_path(DATA_RAW / "external_data/mbie")
    + _files_in_path(DATA_RAW / "external_data/mot")
    + _files_in_path(DATA_RAW / "external_data/kiwirail"),
    "extract_mvr_fleet_data": _files_in_path(DATA_RAW / "external_data/nzta"),
    "extract_vkt_tertile_shares": _files_in_path(DATA_RAW / "external_data/mot"),
    "extract_vehicle_costs_data": _files_in_path(DATA_RAW / "eeca_data/eeud")
    + _files_in_path(DATA_RAW / "eeca_data/tcoe")
    + _files_in_path(DATA_RAW / "external_data/mbie")
    + _files_in_path(DATA_RAW / "external_data/mot")
    + _files_in_path(DATA_RAW / "external_data/kiwirail")
    + _files_in_path(DATA_RAW / "external_data/nrel"),
    "extract_vehicle_future_costs_data": _files_in_path(
        DATA_RAW / "external_data/nrel"
    ),
}


# Stage-1: raw -> stage_1_input_data
STAGE_1: dict[str, list[str]] = {
    "extract_eeud": ["eeud/eeud.csv"],
    "extract_ea_data": [
        "electricity_authority/emi_md.parquet",
        "electricity_authority/emi_distributed_solar.csv",
        "electricity_authority/emi_nsp_concordances.csv",
    ],
    "extract_mbie_data": ["mbie/gen_stack.csv"],
    "extract_nrel_data": ["nrel/future_electricity_costs.csv"],
    "extract_snz_data": ["statsnz/cpi.csv", "statsnz/cgpi.csv"],
    "extract_gic_data": ["gic/gic_production_consumption.csv"],
    "extract_mvr_fleet_data": ["fleet_vkt_pj/vehicle_counts_2023.csv"],
    "extract_fleet_vkt_pj_data": ["fleet_vkt_pj/vkt_by_vehicle_type_and_fuel_2023.csv"],
    "extract_vkt_tertile_shares": ["fleet_vkt_pj/vkt_in_utils_2023.csv"],
    "extract_vehicle_costs_data": ["vehicle_costs/vehicle_costs_by_type_fuel_2023.csv"],
    "extract_vehicle_future_costs_data": [
        "vehicle_costs/vehicle_costs_by_type_fuel_projected_2023.csv"
    ],
}

# Specific dependencies between Stage-1 scripts
STAGE_1_DEPS: dict[str, list[str]] = {
    "extract_fleet_vkt_pj_data": [
        # extract_mvr_fleet_data's output
        "fleet_vkt_pj/vehicle_counts_2023.csv"
    ],
    "extract_vehicle_costs_data": [
        # extract_snz_data's output
        "statsnz/cpi.csv",
        "statsnz/cgpi.csv",
    ],
    "extract_vehicle_future_costs_data": [
        # extract_vehicle_costs_data's output
        "vehicle_costs/vehicle_costs_by_type_fuel_2023.csv",
    ],
}

# Stage-2: base-year calculations
STAGE_2: dict[str, list[str]] = {
    "baseyear_electricity_generation": ["electricity/base_year_electricity_supply.csv"],
    "baseyear_industry_demand": ["industry/baseyear_industry_demand.csv"],
    "baseyear_transport_demand": ["transport/transport_demand_2023.csv"],
    "settings/load_curves": [
        "settings/load_curves.csv",
        "settings/residential_curves.csv",
        "settings.yrfr.csv",
    ],
    "baseyear_residential_demand": ["residential/baseyear_residential_demand.csv"],
}

# Stage-3: scenario demand-growth calculations
STAGE_3: dict[str, list[str]] = {
    "industry/industry_get_demand_growth": ["industry/scenario_demand_growth.csv"],
    "electricity/electricity_new_gen_tech": ["electricity/future_generation_tech.csv"],
}

# Stage-4: VEDA-format CSVs
STAGE_4: dict[str, list[str]] = {
    "create_baseyear_elc_files": ["base_year_elc/existing_tech_capacity.csv"],
    "create_baseyear_tra_files": ["base_year_tra/tra_commodity_definitions.csv"],
}

# Stage-5: final Excel workbooks
STAGE_5: dict[str, list[str]] = {
    "write_excel": [
        "SysSettings.xlsx",
        "VT_TIMESNZ_ELC.xlsx",
        "VT_TIMESNZ_TRA.xlsx",
    ],
}


###############################################################################
# Stage-0: TOML -> config_metadata.csv
###############################################################################


def task_stage_0_parse_tomls():
    """User-config TOMLs -> 'config_metadata.csv' + normalised *.TOMLs.

    Returns the *doit* task dictionary expected by the runtime.  The task is
    considered *up-to-date* when 'config_metadata.csv' exists and is newer than
    **both** the raw TOMLs *and* its own Python script.
    """
    script = STAGE_0_SCRIPTS / "parse_tomls.py"
    return {
        "actions": [_run(str(script))],
        "file_dep": STAGE_0_INPUTS + [script],
        "targets": [CONFIG_META_CSV],
        "clean": True,
    }


###############################################################################
# Stage-1: raw -> stage_1_input_data
###############################################################################


def task_stage_1_extract() -> Iterator[dict]:
    """Stage-1: extractor scripts (one sub-task per source)."""
    for stem, rel_outs in STAGE_1.items():
        script = STAGE_1_SCRIPTS / f"{stem}.py"
        extra_in = [_intermediate_out(p, S1_DIR) for p in STAGE_1_DEPS.get(stem, [])]
        input_files = list(STAGE_1_INPUTS.get(stem, []))
        yield {
            "name": stem,
            "actions": [_run(str(script))],
            "file_dep": [
                script,
                *input_files,
                *extra_in,
                *_files_in_stage(S0_DIR),
            ],
            "targets": [_intermediate_out(rel, S1_DIR) for rel in rel_outs],
            "task_dep": ["stage_0_parse_tomls"],
            "clean": True,
        }


###############################################################################
# Stage-2: base-year calculations
###############################################################################


def task_stage_2_baseyear() -> Iterator[dict]:
    """Stage-2: build calibrated base-year datasets."""
    for stem, rel_outs in STAGE_2.items():
        script = STAGE_2_SCRIPTS / f"{stem}.py"
        yield {
            "name": stem,
            "actions": [_run(str(script))],
            "file_dep": [script]
            + _files_in_stage(S1_DIR)
            + ASSUMPTION_INPUTS
            + CONCORDANCE_INPUTS,
            "targets": [_intermediate_out(rel, S2_DIR) for rel in rel_outs],
            "task_dep": [f"stage_1_extract:{n}" for n in STAGE_1],
            "clean": True,
        }


###############################################################################
# Stage-3: scenario demand-growth calculations
###############################################################################


def task_stage_3_scenarios() -> Iterator[dict]:
    """Stage-3: derive scenario demand-growth assumptions."""
    for rel_script, rel_outs in STAGE_3.items():
        script = STAGE_3_SCRIPTS / f"{rel_script}.py"
        yield {
            "name": rel_script.replace("/", "_"),
            "actions": [_run(str(script))],
            "file_dep": [script]
            + _files_in_stage(S1_DIR)
            + ASSUMPTION_INPUTS
            + CONCORDANCE_INPUTS,
            "targets": [_intermediate_out(rel, S3_DIR) for rel in rel_outs],
            "task_dep": [f"stage_2_baseyear:{n}" for n in STAGE_2],
            "clean": True,
        }


###############################################################################
# Stage-4: VEDA-format CSVs & Excel workbooks
###############################################################################


def task_stage_4_veda_csvs() -> Iterator[dict]:
    """Stage-4: assemble VEDA-ready CSV bundles."""
    for stem, rel_outs in STAGE_4.items():
        script = STAGE_4_SCRIPTS / f"{stem}.py"
        yield {
            "name": stem,
            "actions": [_run(str(script))],
            "file_dep": [script]
            + _files_in_stage(S3_DIR)
            + _files_in_stage(S2_DIR)
            + ASSUMPTION_INPUTS
            + CONCORDANCE_INPUTS,
            "targets": [_intermediate_out(rel, S4_DIR) for rel in rel_outs],
            "task_dep": [f"stage_3_scenarios:{n.replace('/', '_')}" for n in STAGE_3],
            "clean": True,
        }


###############################################################################
# Stage-5: build the Excel workbooks used by VEDA
###############################################################################


def task_stage_5_build_excel():
    """Stage-5: Assemble final Excel workbooks for the VEDA GUI."""
    script = STAGE_4_SCRIPTS / "write_excel.py"
    return {
        "actions": [_run(str(script))],
        "file_dep": [script] + _files_in_stage(S4_DIR) + [CONFIG_META_CSV],
        "targets": [_out(rel) for rel in STAGE_5["write_excel"]],
        "task_dep": [f"stage_4_veda_csvs:{n}" for n in STAGE_4],
        "clean": True,
    }
