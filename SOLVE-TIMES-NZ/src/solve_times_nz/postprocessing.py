"""Turn one completed VEDA result file into release-ready parquet outputs."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pandas as pd


def read_vd(path: Path) -> pd.DataFrame:
    """Read a GDX2VEDA ``.vd`` file without relying on QA-side discovery."""
    dimensions_pattern = re.compile(r"\*\s*Dimensions-")
    columns = None
    skiprows = 0
    with path.open(encoding="utf-8") as source:
        for line in source:
            if dimensions_pattern.search(line):
                columns = line.split("- ", maxsplit=1)[1].strip().split(";")
            if line.startswith('"'):
                break
            skiprows += 1
    if columns is None:
        raise ValueError(f"{path} has no VEDA Dimensions header")
    return pd.read_csv(
        path, skiprows=skiprows, names=columns, header=None, low_memory=False
    )


def _metadata(metadata_dir: Path, name: str) -> pd.DataFrame:
    path = metadata_dir / name
    if not path.is_file():
        raise ValueError(f"Missing PREP reporting metadata: {path}")
    return pd.read_csv(path)


def snapshot_metadata(metadata_dir: Path, run_dir: Path) -> Path:
    """Copy the generated PREP CSV contract into one solver-result release."""
    files = sorted(metadata_dir.glob("*.csv"))
    if not files:
        raise ValueError(f"No PREP reporting CSVs found in {metadata_dir}")
    destination = run_dir / "postprocessed" / "metadata"
    if destination.exists():
        return destination
    destination.mkdir(parents=True)
    for path in files:
        shutil.copy2(path, destination / path.name)
    return destination


def _with_value(df: pd.DataFrame, variable: str, unit: str) -> pd.DataFrame:
    result = df.copy()
    result["Variable"] = variable
    result["Unit"] = unit
    return result.rename(columns={"PV": "Value"})


def _scenario_name(manifest: dict[str, object], manifest_path: Path) -> str:
    """Read the versioned scenario identity declared by the generated case."""
    scenario = manifest.get("scenario_name")
    if not isinstance(scenario, str) or not scenario:
        raise ValueError(f"{manifest_path} has no scenario_name")
    return scenario


def electricity_generation(results: pd.DataFrame, metadata_dir: Path) -> pd.DataFrame:
    """Label electricity generation flows using PREP-owned catalogs."""
    processes = _metadata(metadata_dir, "electricity_generation_processes.csv")
    commodities = _metadata(metadata_dir, "energy_commodities.csv")
    result = results[(results["Attribute"] == "VAR_FOut")].merge(
        processes, on="Process", how="inner", validate="many_to_one"
    )
    result = result.merge(
        commodities, on="Commodity", how="inner", validate="many_to_one"
    )
    return _with_value(result, "Electricity generation", "PJ")


def energy_demand(results: pd.DataFrame, metadata_dir: Path) -> pd.DataFrame:
    """Label demand-device fuel inputs, excluding feedstock as current QA does."""
    processes = _metadata(metadata_dir, "demand_processes.csv")
    commodities = _metadata(metadata_dir, "energy_commodities.csv")
    result = results[(results["Attribute"] == "VAR_FIn")].merge(
        processes, on="Process", how="inner", validate="many_to_one"
    )
    result = result.merge(
        commodities, on="Commodity", how="inner", validate="many_to_one"
    )
    result = result[result["EndUse"] != "Feedstock"]
    return _with_value(result, "Energy demand", "PJ")


def energy_service_demand(results: pd.DataFrame, metadata_dir: Path) -> pd.DataFrame:
    """Label demand-device energy-service outputs using declared commodity units."""
    processes = _metadata(metadata_dir, "demand_processes.csv")
    units = _metadata(metadata_dir, "commodity_units.csv")
    units = units[units["csets"] == "DEM"].rename(
        columns={"commname": "Commodity", "unit": "Unit"}
    )[["Commodity", "Unit"]]
    result = results[(results["Attribute"] == "VAR_FOut")].merge(
        processes, on="Process", how="inner", validate="many_to_one"
    )
    result = result.merge(units, on="Commodity", how="inner", validate="many_to_one")
    result["Variable"] = "Energy service demand"
    return result.rename(columns={"PV": "Value"})


def postprocess_run(run_dir: Path, metadata_dir: Path) -> Path:
    """Write initial post-processing parquet outputs for one completed solver run."""
    files = sorted(run_dir.glob("*.vd"))
    if len(files) != 1:
        raise ValueError(
            f"Expected exactly one .vd file in {run_dir}, found {len(files)}"
        )
    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    scenario = _scenario_name(manifest, manifest_path)
    results = read_vd(files[0])
    results["Scenario"] = scenario
    output = run_dir / "postprocessed"
    output.mkdir(exist_ok=True)
    outputs = {
        "raw_results.parquet": results,
        "elec_generation.parquet": electricity_generation(results, metadata_dir),
        "energy_demand.parquet": energy_demand(results, metadata_dir),
        "energy_service_demand.parquet": energy_service_demand(results, metadata_dir),
    }
    for name, dataframe in outputs.items():
        dataframe.to_parquet(output / name, index=False)
    return output
