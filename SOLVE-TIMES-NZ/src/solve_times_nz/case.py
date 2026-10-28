"""Declarative case resolution and DD export."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INPUT_ROOT = REPOSITORY_ROOT / "PREPARE-TIMES-NZ" / "output"
REQUIRED_DD_FILES = ("ts.dd", "milestonyr.dd", "output.dd")
RUN_TEMPLATE = REPOSITORY_ROOT / "SOLVE-TIMES-NZ" / "templates" / "times.run.template"


class CaseConfigurationError(ValueError):
    """A case manifest or workbook-group definition is invalid."""


@dataclass(frozen=True)
class ResolvedCase:
    """A case with workbook paths fully resolved."""

    manifest_path: Path
    name: str
    input_root: Path
    groups: tuple[str, ...]
    files: tuple[Path, ...]
    manifest: dict[str, Any]


def read_toml(path: Path) -> dict[str, Any]:
    """Read a TOML file with consistent configuration errors."""
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    except FileNotFoundError as error:
        raise CaseConfigurationError(
            f"Configuration file does not exist: {path}"
        ) from error
    except tomllib.TOMLDecodeError as error:
        raise CaseConfigurationError(f"Invalid TOML in {path}: {error}") from error


def _string_list(value: Any, field: str, source: Path) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise CaseConfigurationError(f"{source}: {field} must be a list of strings")
    return value


def _load_manifest(path: Path) -> dict[str, Any]:
    manifest = read_toml(path)
    parent = manifest.get("extends")
    if parent is None:
        return manifest
    if not isinstance(parent, str):
        raise CaseConfigurationError(f"{path}: extends must be a filename")
    base_path = (path.parent / parent).resolve()
    base = _load_manifest(base_path)
    merged = dict(base)
    for key, value in manifest.items():
        if key not in {
            "add_groups",
            "remove_groups",
            "add_files",
            "remove_files",
            "extends",
        }:
            merged[key] = value
    groups = _string_list(base.get("groups", []), "groups", base_path)
    removed = set(
        _string_list(manifest.get("remove_groups", []), "remove_groups", path)
    )
    groups = [group for group in groups if group not in removed]
    groups.extend(_string_list(manifest.get("add_groups", []), "add_groups", path))
    if "groups" in manifest:
        groups = _string_list(manifest["groups"], "groups", path)
    merged["groups"] = groups
    merged["add_files"] = _string_list(manifest.get("add_files", []), "add_files", path)
    merged["remove_files"] = _string_list(
        manifest.get("remove_files", []), "remove_files", path
    )
    return merged


def _group_patterns(
    groups: dict[str, Any], name: str, ancestry: tuple[str, ...] = ()
) -> list[str]:
    if name in ancestry:
        chain = " -> ".join((*ancestry, name))
        raise CaseConfigurationError(f"Input-group inclusion cycle: {chain}")
    definition = groups.get(name)
    if not isinstance(definition, dict):
        raise CaseConfigurationError(f"Unknown input group: {name}")
    patterns: list[str] = []
    for included in _string_list(
        definition.get("includes", []), "includes", Path(name)
    ):
        patterns.extend(_group_patterns(groups, included, (*ancestry, name)))
    patterns.extend(_string_list(definition.get("files", []), "files", Path(name)))
    return patterns


def _expand_patterns(input_root: Path, patterns: list[str]) -> list[Path]:
    files: list[Path] = []
    for pattern in patterns:
        matches = sorted(
            path.resolve() for path in input_root.glob(pattern) if path.is_file()
        )
        if not matches:
            raise CaseConfigurationError(
                f"Input pattern {pattern!r} matched no files below {input_root}"
            )
        files.extend(matches)
    return files


def resolve_case(
    manifest_path: Path,
    input_root: Path = DEFAULT_INPUT_ROOT,
    groups_path: Path | None = None,
) -> ResolvedCase:
    """Resolve a case manifest to an ordered, de-duplicated workbook list."""
    manifest_path = manifest_path.resolve()
    input_root = input_root.resolve()
    if not input_root.is_dir():
        raise CaseConfigurationError(
            f"Input root does not exist: {input_root}. "
            "Run PREPARE-TIMES-NZ first or pass --input-root."
        )
    manifest = _load_manifest(manifest_path)
    name = manifest.get("name")
    if not isinstance(name, str) or not name:
        raise CaseConfigurationError(
            f"{manifest_path}: name must be a non-empty string"
        )
    selected_groups = _string_list(manifest.get("groups", []), "groups", manifest_path)
    if not selected_groups:
        raise CaseConfigurationError(
            f"{manifest_path}: select at least one input group"
        )
    groups_path = (
        groups_path or manifest_path.parents[1] / "config" / "input-groups.toml"
    )
    group_data = read_toml(groups_path).get("groups")
    if not isinstance(group_data, dict):
        raise CaseConfigurationError(f"{groups_path}: expected a [groups] table")
    patterns = [
        pattern
        for group in selected_groups
        for pattern in _group_patterns(group_data, group)
    ]
    patterns.extend(
        _string_list(manifest.get("add_files", []), "add_files", manifest_path)
    )
    files = _expand_patterns(input_root, patterns)
    removals = set(
        _string_list(manifest.get("remove_files", []), "remove_files", manifest_path)
    )
    files = [
        path
        for path in files
        if path.relative_to(input_root).as_posix() not in removals
    ]
    unique_files = tuple(dict.fromkeys(files))
    if not unique_files:
        raise CaseConfigurationError(
            f"{manifest_path}: selected groups resolve to no workbooks"
        )
    unsupported = [
        path for path in unique_files if path.suffix.lower() not in {".xlsx", ".xlsm"}
    ]
    if unsupported:
        raise CaseConfigurationError(
            f"Unsupported workbook type(s): {', '.join(map(str, unsupported))}"
        )
    return ResolvedCase(
        manifest_path, name, input_root, tuple(selected_groups), unique_files, manifest
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _case_settings(case: ResolvedCase) -> tuple[str, str, int]:
    """Return the selected executor and basic TIMES settings for a case."""
    solve = case.manifest.get("solve", {})
    if not isinstance(solve, dict):
        raise CaseConfigurationError(
            f"{case.manifest_path}: [solve] must be a TOML table"
        )
    executor = solve.get("executor")
    if not isinstance(executor, str) or not executor:
        raise CaseConfigurationError(
            f"{case.manifest_path}: [solve].executor must be a non-empty string"
        )
    times = case.manifest.get("times", {})
    if not isinstance(times, dict):
        raise CaseConfigurationError(
            f"{case.manifest_path}: [times] must be a TOML table"
        )
    solver = times.get("solver", "cplex")
    reslim = times.get("reslim", 50000)
    if not isinstance(solver, str) or not solver:
        raise CaseConfigurationError(
            f"{case.manifest_path}: [times].solver must be a non-empty string"
        )
    if not isinstance(reslim, int) or isinstance(reslim, bool) or reslim < 0:
        raise CaseConfigurationError(
            f"{case.manifest_path}: [times].reslim must be a non-negative integer"
        )
    return executor, solver, reslim


def _render_run_file(
    case: ResolvedCase, output_dir: Path, solver: str, reslim: int
) -> Path:
    """Render the project-owned, path-independent TIMES run program."""
    try:
        template = RUN_TEMPLATE.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise RuntimeError(f"Missing TIMES run template: {RUN_TEMPLATE}") from error
    rendered = (
        template.replace("__CASE_NAME__", case.name)
        .replace("__SOLVER__", solver)
        .replace("__RESLIM__", str(reslim))
    )
    run_path = output_dir / f"{case.name}.run"
    run_path.write_text(rendered, encoding="utf-8")
    return run_path


def build_case(
    case: ResolvedCase,
    output_dir: Path,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> Path:
    """Replace a generated case directory with a fresh DD export."""
    output_dir = output_dir.resolve()
    if output_dir.exists():
        if not output_dir.is_dir() or output_dir.is_symlink():
            raise CaseConfigurationError(
                f"Refusing to replace non-directory or symlink output path: {output_dir}"
            )
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    command = [
        sys.executable,
        "-m",
        "solve_times_nz.xl2times_compat",
        *(str(path) for path in case.files),
        "--dd",
        "--output_dir",
        str(output_dir),
    ]
    try:
        runner(command, check=True, text=True, cwd=output_dir)
    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            f"xl2times DD export failed with exit code {error.returncode}"
        ) from error
    missing = [name for name in REQUIRED_DD_FILES if not (output_dir / name).is_file()]
    if missing:
        raise RuntimeError(
            f"xl2times did not create required DD file(s): {', '.join(missing)}"
        )
    executor, solver, reslim = _case_settings(case)
    run_path = _render_run_file(case, output_dir, solver, reslim)
    manifest = {
        "case_name": case.name,
        "built_at": datetime.now(UTC).isoformat(),
        "input_root": str(case.input_root),
        "case_manifest": str(case.manifest_path),
        "groups": list(case.groups),
        "inputs": [
            {
                "path": path.relative_to(case.input_root).as_posix(),
                "sha256": _sha256(path),
            }
            for path in case.files
        ],
        "command": command,
        "python_version": sys.version,
        "xl2times": "0.3.0",
        "executor": executor,
        "times": {"solver": solver, "reslim": reslim},
        "run_file": run_path.name,
        "run_template_sha256": _sha256(RUN_TEMPLATE),
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return output_dir
