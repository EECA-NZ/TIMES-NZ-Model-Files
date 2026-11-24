"""Build named releases from raw/labelled Parquets and prepared summary CSVs."""

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
from publish_times_nz.reporting import read_summary_csv


class ReleaseBuildError(ValueError):
    """Raised when source results cannot form a release."""


def build_release(
    release_name: str,
    source_directories: list[Path],
    releases_root: Path,
    *,
    definition: dict[str, object] | None = None,
) -> ReleaseBundle:
    """Build one release from one-scenario solver postprocessing directories."""
    sources = _source_directories(source_directories)
    for source in sources:
        for path in _result_files(source):
            relative = path.relative_to(source)
            if relative != Path("raw_results.parquet") and (
                len(relative.parts) < 2
                or (relative.parts[0], relative.suffix)
                not in {("labelled", ".parquet"), ("summaries", ".csv")}
                or relative.name == "raw_results.parquet"
            ):
                raise ReleaseBuildError(
                    f"Invalid result layout: {path}; expected labelled/ Parquets, "
                    "summaries/ CSVs and raw_results.parquet at the result root"
                )
    scenario_ids_by_source = {
        source: _scenario_ids(_result_files(source)) for source in sources
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
    return _publish(release_name, _source_tables(sources), manifest, releases_root)


def import_legacy_release(
    release_name: str,
    source_directory: Path,
    releases_root: Path,
    legacy_source: str | None = None,
) -> ReleaseBundle:
    """Import one already scenario-batched legacy result directory."""
    source = _source_directories([source_directory])[0]
    tables = {}
    for relative, source_tables in _source_tables([source]).items():
        # Legacy archives keep labelled datasets beside raw_results.parquet.
        destination = (
            Path("labelled") / relative
            if len(relative.parts) == 1 and relative.name != "raw_results.parquet"
            else relative
        )
        if destination in tables:
            raise ReleaseBuildError(f"Duplicate legacy dataset: {destination}")
        tables[destination] = source_tables
    scenario_ids = _scenario_ids(_result_files(source))
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


def _result_files(source: Path) -> tuple[Path, ...]:
    return tuple(
        sorted((*_parquet_files(source), *(source / "summaries").rglob("*.csv")))
    )


def _scenario_ids(result_files: tuple[Path, ...]) -> set[str]:
    scenario_ids: set[str] = set()
    for result_file in result_files:
        table = (
            pa.Table.from_pandas(read_summary_csv(result_file), preserve_index=False)
            if result_file.suffix == ".csv"
            else pq.read_table(result_file, columns=["Scenario"])
        )
        if "Scenario" not in table.column_names:
            raise ReleaseBuildError(f"Result is missing Scenario column: {result_file}")
        scenario_ids.update(value.as_py() for value in table["Scenario"].unique())
    if not scenario_ids or not all(
        isinstance(value, str) and value for value in scenario_ids
    ):
        raise ReleaseBuildError("Result Scenario values must be non-empty strings")
    return scenario_ids


def _source_tables(sources: list[Path]) -> dict[Path, list[pa.Table]]:
    tables: dict[Path, list[pa.Table]] = defaultdict(list)
    for source in sources:
        for result_file in _result_files(source):
            table = (
                pa.Table.from_pandas(
                    read_summary_csv(result_file), preserve_index=False
                )
                if result_file.suffix == ".csv"
                else pq.read_table(result_file)
            )
            tables[result_file.relative_to(source)].append(table)
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
            destination = staging_path / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            try:
                table = pa.concat_tables(source_tables)
            except pa.ArrowInvalid as error:
                raise ReleaseBuildError(
                    f"Result schemas differ for {relative_path}"
                ) from error
            if relative_path.suffix == ".csv":
                table.to_pandas().to_csv(destination, index=False)
            else:
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


def _validate_release_name(release_name: str) -> None:
    if not release_name or Path(release_name).name != release_name:
        raise ReleaseBuildError(f"Invalid release name: {release_name}")
