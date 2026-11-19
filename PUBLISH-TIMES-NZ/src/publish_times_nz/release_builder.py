"""Build named release directories from solver or legacy Parquet results."""

from __future__ import annotations

import json
import shutil
import uuid
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from publish_times_nz.release_bundle import (
    RELEASE_FORMAT_VERSION,
    ReleaseBundle,
    load_bundle,
)


class ReleaseBuildError(ValueError):
    """Raised when source Parquets cannot form a release."""


def build_release(
    release_name: str,
    source_directories: list[Path],
    releases_root: Path,
    *,
    definition: dict[str, object] | None = None,
) -> ReleaseBundle:
    """Build one release from one-scenario solver postprocessing directories."""
    sources = _source_directories(source_directories)
    scenario_ids_by_source = {
        source: _scenario_ids(_parquet_files(source)) for source in sources
    }
    for source, scenario_ids in scenario_ids_by_source.items():
        if len(scenario_ids) != 1:
            raise ReleaseBuildError(
                f"Solver source must contain one scenario: {source} "
                f"has {sorted(scenario_ids)}"
            )
    scenario_ids = [next(iter(ids)) for ids in scenario_ids_by_source.values()]
    if len(scenario_ids) != len(set(scenario_ids)):
        raise ReleaseBuildError(
            "Selected solver sources contain duplicate scenario IDs"
        )
    if definition is not None:
        expected = [
            f"{case}-v{definition['workspace_version']}"
            for case in definition["scenarios"]
        ]
        if scenario_ids != expected:
            raise ReleaseBuildError(
                f"Parquet scenarios {scenario_ids} "
                f"do not match bundle definition {expected}"
            )

    tables = _source_tables(sources)
    lineage = {
        "type": "solver_runs",
        "runs": [source.parent.name for source in sources],
    }
    if definition is not None:
        lineage["definition"] = definition
    manifest = _manifest(release_name, scenario_ids, lineage)
    if definition is not None:
        for scenario, label in zip(
            manifest["scenarios"], definition["scenarios"].values(), strict=True
        ):
            scenario["label"] = label
    return _publish(release_name, tables, manifest, releases_root)


def import_legacy_release(
    release_name: str,
    source_directory: Path,
    releases_root: Path,
    legacy_source: str | None = None,
) -> ReleaseBundle:
    """Import one already scenario-batched legacy result directory."""
    source = _source_directories([source_directory])[0]
    tables = _source_tables([source])
    scenario_ids = _scenario_ids(_parquet_files(source))
    manifest = _manifest(
        release_name,
        sorted(scenario_ids),
        {"type": "legacy", "legacy_source": legacy_source or str(source)},
    )
    return _publish(release_name, tables, manifest, releases_root)


def _source_directories(source_directories: list[Path]) -> list[Path]:
    if not source_directories:
        raise ReleaseBuildError("At least one source directory is required")
    sources = [source.resolve() for source in source_directories]
    for source in sources:
        if not source.is_dir():
            raise ReleaseBuildError(f"Source directory does not exist: {source}")
        if not _parquet_files(source):
            raise ReleaseBuildError(
                f"Source directory contains no Parquet files: {source}"
            )
    return sources


def _parquet_files(source: Path) -> tuple[Path, ...]:
    return tuple(sorted(source.rglob("*.parquet")))


def _scenario_ids(parquet_files: tuple[Path, ...]) -> set[str]:
    scenario_ids: set[str] = set()
    for parquet_file in parquet_files:
        table = pq.read_table(parquet_file, columns=["Scenario"])
        if "Scenario" not in table.column_names:
            raise ReleaseBuildError(
                f"Parquet is missing Scenario column: {parquet_file}"
            )
        scenario_ids.update(value.as_py() for value in table["Scenario"].unique())
    if not scenario_ids or not all(
        isinstance(value, str) and value for value in scenario_ids
    ):
        raise ReleaseBuildError("Parquet Scenario values must be non-empty strings")
    return scenario_ids


def _source_tables(sources: list[Path]) -> dict[Path, list[pa.Table]]:
    tables: dict[Path, list[pa.Table]] = defaultdict(list)
    for source in sources:
        for parquet_file in _parquet_files(source):
            tables[parquet_file.relative_to(source)].append(pq.read_table(parquet_file))
    return tables


def _manifest(
    release_name: str, scenario_ids: list[str], source: dict[str, object]
) -> dict[str, object]:
    return {
        "format_version": RELEASE_FORMAT_VERSION,
        "release_name": release_name,
        "scenarios": [
            {"id": scenario_id, "label": scenario_id} for scenario_id in scenario_ids
        ],
        "source": source,
        "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }


def _publish(
    release_name: str,
    tables: dict[Path, list[pa.Table]],
    manifest: dict[str, object],
    releases_root: Path,
) -> ReleaseBundle:
    _validate_release_name(release_name)
    release_path = releases_root / release_name
    if release_path.exists():
        raise ReleaseBuildError(f"Release already exists: {release_path}")

    releases_root.mkdir(parents=True, exist_ok=True)
    staging_path = releases_root / f".{release_name}.{uuid.uuid4().hex}.staging"
    try:
        for relative_path, source_tables in tables.items():
            destination = _destination(staging_path, relative_path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            try:
                table = pa.concat_tables(source_tables)
            except pa.ArrowInvalid as error:
                raise ReleaseBuildError(
                    f"Parquet schemas differ for {relative_path}"
                ) from error
            pq.write_table(table, destination, compression="zstd")
        (staging_path / "release-manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
        bundle = load_bundle(staging_path)
        staging_path.rename(release_path)
        return ReleaseBundle(release_path, bundle.manifest)
    except Exception:
        shutil.rmtree(staging_path, ignore_errors=True)
        raise


def _destination(staging_path: Path, relative_path: Path) -> Path:
    if relative_path == Path("raw_results.parquet"):
        return staging_path / "raw" / relative_path
    return staging_path / "labelled" / relative_path


def _validate_release_name(release_name: str) -> None:
    if not release_name or Path(release_name).name != release_name:
        raise ReleaseBuildError(f"Invalid release name: {release_name}")
