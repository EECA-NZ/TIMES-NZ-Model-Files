"""Resolve portable bundle definitions to completed local solver runs."""

from __future__ import annotations

import json
import tomllib
from datetime import datetime
from pathlib import Path

from publish_times_nz.release_builder import ReleaseBuildError, build_release
from publish_times_nz.release_bundle import ReleaseBundle


def load_definition(path: Path) -> dict[str, object]:
    """Read a bundle name and ordered case-to-display-label mappings."""
    with path.open("rb") as source:
        definition = tomllib.load(source)
    if set(definition) != {"name", "scenarios"}:
        raise ReleaseBuildError(
            "Bundle definition must contain only name and scenarios"
        )
    name = definition["name"]
    scenarios = definition["scenarios"]
    if not isinstance(name, str) or name in {"", ".", ".."} or Path(name).name != name:
        raise ReleaseBuildError("Bundle name must be a single directory name")
    if (
        not isinstance(scenarios, dict)
        or not scenarios
        or not all(
            isinstance(case, str)
            and case.strip()
            and isinstance(label, str)
            and label.strip()
            for case, label in scenarios.items()
        )
    ):
        raise ReleaseBuildError(
            "Bundle scenarios must map non-empty case names to labels"
        )
    return definition


def select_runs(
    scenarios: list[str],
    version: str,
    runs: dict[Path, dict[str, object]],
) -> list[Path]:
    """Select the newest completed solve for each case, preserving definition order."""
    selected = []
    for case in scenarios:
        candidates = []
        for run_dir, manifest in runs.items():
            if (
                manifest.get("case_name") != case
                or manifest.get("scenario_name") != f"{case}-v{version}"
                or manifest.get("execution", {}).get("status") != "completed"
                or manifest.get("postprocessing", {}).get("status") != "completed"
            ):
                continue
            try:
                completed_at = datetime.fromisoformat(
                    manifest["execution"]["completed_at"]
                )
                if completed_at.tzinfo is None:
                    raise ValueError("Timestamp has no timezone")
            except (KeyError, TypeError, ValueError) as error:
                raise ReleaseBuildError(
                    f"Invalid solve completion timestamp: {run_dir}"
                ) from error
            candidates.append((completed_at, run_dir))
        if not candidates:
            raise ReleaseBuildError(
                f"No completed, postprocessed run for {case}-v{version}; "
                "solve it or rerun postprocessing for an existing run"
            )
        latest = max(timestamp for timestamp, _ in candidates)
        newest = [run_dir for timestamp, run_dir in candidates if timestamp == latest]
        if len(newest) != 1:
            raise ReleaseBuildError(
                f"Multiple runs have the latest completion time for {case}"
            )
        selected.append(newest[0])
    return selected


def build_bundle(
    definition_path: Path, repository_root: Path, releases_root: Path
) -> ReleaseBundle:
    """Resolve the current workspace's cases and assemble an immutable release."""
    definition = load_definition(definition_path)
    with (repository_root / "pyproject.toml").open("rb") as source:
        version = tomllib.load(source)["project"]["version"]
    solves_root = repository_root / "SOLVE-TIMES-NZ" / "build" / "solves"
    runs = {}
    for manifest_path in sorted(solves_root.glob("*/manifest.json")):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ReleaseBuildError(
                f"Invalid solve manifest: {manifest_path}"
            ) from error
        runs[manifest_path.parent] = manifest
    selected = select_runs(list(definition["scenarios"]), version, runs)
    for run_dir in selected:
        output = run_dir / "postprocessed"
        manifest = runs[run_dir]
        files = manifest["postprocessing"].get("files", [])
        if not files or not all((output / name).is_file() for name in files):
            raise ReleaseBuildError(
                f"Completed postprocessing outputs are missing: {run_dir}"
            )
        print(f"{manifest['scenario_name']}: {run_dir.name}")
    return build_release(
        f"v{version}-{definition['name']}",
        [run_dir / "postprocessed" for run_dir in selected],
        releases_root,
        definition={**definition, "workspace_version": version},
    )
