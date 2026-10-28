"""Local executor configuration and safe staging of generated TIMES cases."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from solve_times_nz.case import REQUIRED_DD_FILES, CaseConfigurationError, read_toml


@dataclass(frozen=True)
class Executor:
    """The three machine-local paths needed to stage a TIMES case."""

    name: str
    staging_root: Path
    gams_system_dir: Path
    times_source_dir: Path


def load_executor(path: Path, name: str) -> Executor:
    """Load and validate one local executor binding."""
    if not path.is_file():
        raise CaseConfigurationError(
            f"Local executor configuration does not exist: {path}. "
            "Copy config/solve.local.example.toml to config/solve.local.toml and edit it."
        )
    executors = read_toml(path).get("executors")
    if not isinstance(executors, dict) or not isinstance(executors.get(name), dict):
        raise CaseConfigurationError(f"{path}: unknown executor {name!r}")
    config = executors[name]
    staging_root = config.get("staging_root")
    gams_system_dir = config.get("gams_system_dir")
    times_source_dir = config.get("times_source_dir")
    if not isinstance(staging_root, str) or not staging_root:
        raise CaseConfigurationError(
            f"{path}: executors.{name}.staging_root must be a non-empty path"
        )
    if not isinstance(gams_system_dir, str) or not gams_system_dir:
        raise CaseConfigurationError(
            f"{path}: executors.{name}.gams_system_dir must be a non-empty path"
        )
    if not isinstance(times_source_dir, str) or not times_source_dir:
        raise CaseConfigurationError(
            f"{path}: executors.{name}.times_source_dir must be a non-empty path"
        )
    return Executor(
        name,
        Path(staging_root),
        Path(gams_system_dir),
        Path(times_source_dir),
    )


def stage_case(case_dir: Path, local_config: Path, run_id: str | None = None) -> Path:
    """Copy a complete generated case to its configured executor staging root."""
    case_dir = case_dir.resolve()
    manifest_path = case_dir / "manifest.json"
    if not manifest_path.is_file():
        raise CaseConfigurationError(f"Generated case has no manifest: {case_dir}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise CaseConfigurationError(
            f"Invalid generated-case manifest: {manifest_path}"
        ) from error
    case_name = manifest.get("case_name")
    executor_name = manifest.get("executor")
    run_file = manifest.get("run_file")
    if not all(
        isinstance(value, str) and value
        for value in (case_name, executor_name, run_file)
    ):
        raise CaseConfigurationError(
            f"{manifest_path}: case_name, executor, and run_file are required"
        )
    executor = load_executor(local_config, executor_name)
    missing = [
        filename
        for filename in (*REQUIRED_DD_FILES, run_file)
        if not (case_dir / filename).is_file()
    ]
    if missing:
        raise CaseConfigurationError(
            f"Generated case is incomplete; missing: {', '.join(missing)}"
        )
    if not executor.staging_root.is_dir():
        raise CaseConfigurationError(
            f"Executor staging root does not exist: {executor.staging_root}"
        )
    safe_run_id = run_id or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    if not safe_run_id.replace("-", "").replace("_", "").isalnum():
        raise CaseConfigurationError(
            "run ID may contain only letters, numbers, '-' and '_'"
        )
    destination = executor.staging_root / f"{case_name}-{safe_run_id}"
    if destination.exists():
        raise CaseConfigurationError(
            f"Refusing to overwrite existing staged run: {destination}"
        )
    shutil.copytree(case_dir, destination)
    staged_manifest = json.loads(
        (destination / "manifest.json").read_text(encoding="utf-8")
    )
    staged_manifest["staging"] = {
        "executor": executor.name,
        "staged_at": datetime.now(UTC).isoformat(),
        "source_case_dir": str(case_dir),
    }
    (destination / "manifest.json").write_text(
        json.dumps(staged_manifest, indent=2) + "\n", encoding="utf-8"
    )
    return destination
