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
    """A machine-local binding capable of running one or more toolchains."""

    name: str
    kind: str
    staging_root: Path
    toolchains: tuple[str, ...]
    settings: dict[str, str]


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
    kind = config.get("kind")
    staging_root = config.get("staging_root")
    toolchains = config.get("toolchains")
    if not isinstance(kind, str) or not kind:
        raise CaseConfigurationError(f"{path}: executors.{name}.kind must be a string")
    if not isinstance(staging_root, str) or not staging_root:
        raise CaseConfigurationError(
            f"{path}: executors.{name}.staging_root must be a non-empty path"
        )
    if not isinstance(toolchains, list) or not all(
        isinstance(item, str) and item for item in toolchains
    ):
        raise CaseConfigurationError(
            f"{path}: executors.{name}.toolchains must be a list of strings"
        )
    settings = {
        key: value
        for key, value in config.items()
        if key not in {"kind", "staging_root", "toolchains"} and isinstance(value, str)
    }
    return Executor(name, kind, Path(staging_root), tuple(toolchains), settings)


def stage_case(case_dir: Path, executor: Executor, run_id: str | None = None) -> Path:
    """Copy a complete generated case to a new executor-local run directory."""
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
    toolchain = manifest.get("toolchain")
    run_file = manifest.get("run_file")
    if not all(
        isinstance(value, str) and value for value in (case_name, toolchain, run_file)
    ):
        raise CaseConfigurationError(
            f"{manifest_path}: case_name, toolchain, and run_file are required"
        )
    if toolchain not in executor.toolchains:
        raise CaseConfigurationError(
            f"Executor {executor.name!r} does not support toolchain {toolchain!r}"
        )
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
        "kind": executor.kind,
        "staged_at": datetime.now(UTC).isoformat(),
        "source_case_dir": str(case_dir),
    }
    (destination / "manifest.json").write_text(
        json.dumps(staged_manifest, indent=2) + "\n", encoding="utf-8"
    )
    return destination
