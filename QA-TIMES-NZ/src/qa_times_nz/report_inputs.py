"""Select prepared RELEASE or SOLVE inputs for one configured QA comparison."""

import json
import math
import re
import tomllib
from datetime import datetime
from pathlib import Path

import pandas as pd

from publish_times_nz.bundle_definition import select_runs
from publish_times_nz.release_bundle import load_bundle
from publish_times_nz.reporting import read_summary_csv

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def _validate_selection(selection: dict) -> None:
    """Require explicit source-specific selectors, without alternate search paths."""
    if not isinstance(selection, dict) or selection.get("source") not in (
        "RELEASE",
        "SOLVE",
    ):
        raise ValueError("Expected source = RELEASE or SOLVE for each input")
    required = {"source", "scenario"}
    optional = {"label"}
    if selection["source"] == "RELEASE":
        required.add("release")
    else:
        optional.add("timestamp")
    if not required <= selection.keys() or selection.keys() - required - optional:
        raise ValueError(f"Expected {sorted(required)} and optional {sorted(optional)}")
    for field, value in selection.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Expected non-empty text for {field}")
    for field in required - {"source"}:
        value = selection[field]
        if value in {".", ".."} or "/" in value or "\\" in value:
            raise ValueError(f"Expected a single {field} identifier: {value}")
    if "timestamp" in selection:
        _validate_timestamp(selection["timestamp"])


def _validate_timestamp(timestamp: str) -> None:
    """Match the UTC token used in the run directory, including a valid date."""
    if not re.fullmatch(r"\d{8}T\d{6}Z", timestamp):
        raise ValueError("Expected a SOLVE timestamp in YYYYMMDDTHHMMSSZ form")
    datetime.strptime(timestamp, "%Y%m%dT%H%M%SZ")


def load_config(*, dev: bool = False) -> dict:
    """Load main by default; a missing requested developer config is an error."""
    name = "report_config_dev.toml" if dev else "report_config.toml"
    path = REPOSITORY_ROOT / "QA-TIMES-NZ" / name
    if not path.is_file():
        raise FileNotFoundError(f"Missing QA configuration: {path}")
    with path.open("rb") as source:
        config = tomllib.load(source)
    if set(config) != {"baseline", "candidate", "tolerance"}:
        raise ValueError(
            "Expected baseline, candidate and tolerance in QA configuration"
        )
    tolerance = config["tolerance"]
    if (
        isinstance(tolerance, bool)
        or not isinstance(tolerance, (int, float))
        or not 0 <= tolerance < math.inf
    ):
        raise ValueError("Expected a finite, non-negative relative tolerance")
    for role in ["baseline", "candidate"]:
        _validate_selection(config[role])
    return config


def _result_path(root: Path, relative: str) -> Path:
    """Keep declared outputs and requested datasets beneath the result root."""
    if (
        not isinstance(relative, str)
        or not relative
        or Path(relative).is_absolute()
        or ".." in Path(relative).parts
        or "\\" in relative
    ):
        raise ValueError(f"Expected a relative result path: {relative}")
    return root / relative


# Keep the two supported layouts and their selection rules together.
# pylint: disable-next=too-many-locals,too-many-branches,too-many-statements
def resolve_input(selection: dict) -> dict:
    """Resolve one explicit source, retaining its manifest and canonical identity."""
    _validate_selection(selection)
    with (REPOSITORY_ROOT / "pyproject.toml").open("rb") as source:
        workspace_version = tomllib.load(source)["project"]["version"]
    timestamp = selection.get("timestamp")
    if selection["source"] == "RELEASE":
        bundle = load_bundle(
            REPOSITORY_ROOT / "PUBLISH-TIMES-NZ/releases" / selection["release"]
        )
        labels = {entry["id"]: entry["label"] for entry in bundle.scenarios}
        scenario = selection["scenario"]
        if scenario not in labels:
            raise ValueError(
                f"Scenario {scenario} is absent from release {bundle.path}"
            )
        root = bundle.path
        manifest_path = root / "release-manifest.json"
        manifest = bundle.manifest
        definition = manifest["source"].get("definition", {})
        if not isinstance(definition, dict):
            raise ValueError(f"Invalid release definition metadata: {manifest_path}")
        version = definition.get("workspace_version")
        files = [path.relative_to(root).as_posix() for path in bundle.result_files]
        label = labels[scenario]
    else:
        runs = {}
        solves = REPOSITORY_ROOT / "SOLVE-TIMES-NZ/build/solves"
        for path in sorted(solves.glob("*/manifest.json")):
            if timestamp and not path.parent.name.endswith(f"-{timestamp}"):
                continue
            try:
                manifest = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid SOLVE manifest: {path}") from error
            if not isinstance(manifest, dict) or any(
                field in manifest and not isinstance(manifest[field], dict)
                for field in ["execution", "postprocessing"]
            ):
                raise ValueError(f"Invalid SOLVE manifest: {path}")
            runs[path.parent] = manifest
        case = selection["scenario"]
        if timestamp:
            matches = [
                path
                for path, manifest in runs.items()
                if manifest.get("case_name") == case
            ]
            if len(matches) != 1:
                raise ValueError(
                    f"Expected one SOLVE run for {case} at {timestamp}; found {len(matches)}"
                )
            run = matches[0]
            manifest = runs[run]
            scenario = manifest.get("scenario_name")
            prefix = f"{case}-v"
            if (
                not isinstance(scenario, str)
                or not scenario.startswith(prefix)
                or scenario == prefix
            ):
                raise ValueError(f"Missing or invalid versioned scenario ID: {run}")
            version = scenario[len(prefix) :]
            # Only the pinned run is eligible; never fall back after a failed pin.
            select_runs([case], version, {run: manifest})
        else:
            run = select_runs([case], workspace_version, runs)[0]
            manifest = runs[run]
            scenario = manifest["scenario_name"]
            version = workspace_version
        timestamp = run.name.rsplit("-", 1)[-1]
        _validate_timestamp(timestamp)
        root = run / "postprocessed"
        manifest_path = run / "manifest.json"
        files = manifest["postprocessing"].get("files")
        if not isinstance(files, list) or not files:
            raise ValueError(f"Missing post-processing file list: {manifest_path}")
        if not all(_result_path(root, name).is_file() for name in files):
            raise ValueError(f"Completed post-processing outputs are missing: {run}")
        labels = {scenario: scenario}
        label = scenario
    if not any(
        name.startswith("summaries/") and name.endswith(".csv") for name in files
    ):
        raise ValueError(f"No prepared summary CSVs: {root}")
    return {
        "source": selection["source"],
        "scenario": scenario,
        "label": selection.get("label", label),
        "result_root": root,
        "manifest_path": manifest_path,
        "manifest": manifest,
        "version": version,
        "workspace_version": workspace_version,
        "timestamp": timestamp,
        "files": files,
        "scenario_ids": list(labels),
    }


def resolve_inputs(*, dev: bool = False) -> dict:
    """Resolve both roles separately and print the exact inputs for later pinning."""
    config = load_config(dev=dev)
    resolved = {"tolerance": config["tolerance"]}
    for role in ["baseline", "candidate"]:
        selected = resolve_input(config[role])
        resolved[role] = selected
        print(
            f"{role}: {selected['source']} {selected['result_root']} / "
            f"{selected['scenario']} (version={selected['version'] or 'not recorded'}, "
            f"workspace={selected['workspace_version']}, "
            f"timestamp={selected['timestamp'] or 'not applicable'})"
        )
    return resolved


def load_summary(selected: dict, relative: str) -> pd.DataFrame | None:
    """Read one scenario's prepared rows; optional missing data stays absent."""
    path = _result_path(selected["result_root"], relative)
    if not relative.startswith("summaries/") or path.suffix != ".csv":
        raise ValueError("Expected a summaries/<subject>/<table>.csv dataset path")
    if relative not in selected["files"]:
        return None
    frame = read_summary_csv(path)
    if not set(frame.Scenario) <= set(selected["scenario_ids"]):
        raise ValueError(f"Undeclared summary scenarios: {path}")
    frame = frame.loc[frame.Scenario.eq(selected["scenario"])].copy()
    return None if frame.empty else frame
