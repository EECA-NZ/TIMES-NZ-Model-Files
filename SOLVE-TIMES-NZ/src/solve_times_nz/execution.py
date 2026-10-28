"""Local executor configuration and safe staging of generated TIMES cases."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

from solve_times_nz.case import (
    REPOSITORY_ROOT,
    REQUIRED_DD_FILES,
    CaseConfigurationError,
    read_toml,
)

RESULTS_ROOT = REPOSITORY_ROOT / "SOLVE-TIMES-NZ" / "build" / "solves"
VEDA_RESULT_SUFFIXES = {".vd", ".vde", ".vds", ".vdt"}


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
            "Copy config/solve.local.example.toml to "
            "config/solve.local.toml and edit it."
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


def _stage_case(case_dir: Path, local_config: Path, run_id: str | None = None) -> Path:
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


def _windows_path(path: Path) -> str:
    """Convert a WSL-visible Windows path for a native Windows process."""
    try:
        result = subprocess.run(
            ["wslpath", "-w", str(path)],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as error:
        raise CaseConfigurationError(
            "Windows solving requires WSL and its wslpath utility"
        ) from error
    except subprocess.CalledProcessError as error:
        raise CaseConfigurationError(
            f"Cannot convert executor path to a Windows path: {path}"
        ) from error
    return result.stdout.strip()


def _record_execution(destination: Path, execution: dict[str, object]) -> None:
    """Add native-solver execution status to a staged case manifest."""
    manifest_path = destination / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["execution"] = execution
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def _staged_case_settings(destination: Path) -> tuple[str, str, str]:
    """Return the case name, executor name, and run file from a staged manifest."""
    manifest_path = destination / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
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
    return case_name, executor_name, run_file


def _gams_command(
    destination: Path,
    executor: Executor,
    case_name: str,
    run_file: str,
    windows_path: Callable[[Path], str],
) -> list[str]:
    """Construct the native Windows GAMS command for one staged case."""
    gams = executor.gams_system_dir / "gams.exe"
    gdx2veda = executor.gams_system_dir / "gdx2veda.exe"
    restart = executor.times_source_dir / "_times.g00"
    veda_directives = executor.times_source_dir / "times2veda.vdd"
    if not gams.is_file():
        raise CaseConfigurationError(f"GAMS executable does not exist: {gams}")
    if not gdx2veda.is_file():
        raise CaseConfigurationError(f"GDX2VEDA executable does not exist: {gdx2veda}")
    if not restart.is_file():
        raise CaseConfigurationError(f"TIMES restart file does not exist: {restart}")
    if not veda_directives.is_file():
        raise CaseConfigurationError(
            f"TIMES GDX2VEDA directives do not exist: {veda_directives}"
        )
    destination_windows = windows_path(destination)
    source_windows = windows_path(executor.times_source_dir)
    command_text = (
        f"cd /d {destination_windows} "
        "&& if not exist GAMSSAVE mkdir GAMSSAVE "
        f"&& GAMS {run_file} IDIR={source_windows} "
        f"GDX=GAMSSAVE\\{case_name} PS=99999 "
        f"R={source_windows}\\_times LO=1 "
        f"&& GDX2VEDA GAMSSAVE\\{case_name} "
        f"{source_windows}\\times2veda.vdd {case_name}"
    )
    return ["cmd.exe", "/d", "/c", command_text]


def _copy_veda_results(destination: Path) -> Path:
    """Copy VEDA result files from a Windows run into the ignored build tree."""
    result_dir = RESULTS_ROOT / destination.name
    if result_dir.exists():
        raise RuntimeError(f"Refusing to overwrite solver results: {result_dir}")
    result_files = [
        path
        for path in destination.iterdir()
        if path.is_file() and path.suffix.lower() in VEDA_RESULT_SUFFIXES
    ]
    if not result_files:
        raise RuntimeError(f"GDX2VEDA produced no VEDA result files in {destination}")
    result_dir.mkdir(parents=True)
    for result_file in result_files:
        shutil.copy2(result_file, result_dir / result_file.name)
    manifest = json.loads((destination / "manifest.json").read_text(encoding="utf-8"))
    manifest["results"] = {
        "copied_at": datetime.now(UTC).isoformat(),
        "source_run_dir": str(destination),
        "files": sorted(path.name for path in result_files),
    }
    (result_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return result_dir


def solve_case(
    case_dir: Path,
    local_config: Path,
    run_id: str | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    windows_path: Callable[[Path], str] = _windows_path,
) -> Path:
    """Stage a case, solve it, and copy VEDA result files into the build tree."""
    destination = _stage_case(case_dir, local_config, run_id)
    case_name, executor_name, run_file = _staged_case_settings(destination)
    executor = load_executor(local_config, executor_name)
    command = _gams_command(destination, executor, case_name, run_file, windows_path)
    started_at = datetime.now(UTC).isoformat()
    try:
        runner(command, check=True)
    except subprocess.CalledProcessError as error:
        _record_execution(
            destination,
            {
                "started_at": started_at,
                "completed_at": datetime.now(UTC).isoformat(),
                "status": "failed",
                "exit_code": error.returncode,
                "command": command,
            },
        )
        raise RuntimeError(
            f"GAMS solve failed with exit code {error.returncode}; "
            f"staged run retained at {destination}"
        ) from error
    _record_execution(
        destination,
        {
            "started_at": started_at,
            "completed_at": datetime.now(UTC).isoformat(),
            "status": "completed",
            "exit_code": 0,
            "command": command,
        },
    )
    try:
        return _copy_veda_results(destination)
    except RuntimeError as error:
        _record_execution(
            destination,
            {
                "started_at": started_at,
                "completed_at": datetime.now(UTC).isoformat(),
                "status": "export_failed",
                "command": command,
                "error": str(error),
            },
        )
        raise
