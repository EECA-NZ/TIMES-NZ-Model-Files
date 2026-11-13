"""Tests for the public release-bundle seam."""

import json

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from publish_times_nz.release_bundle import (
    RELEASE_FORMAT_VERSION,
    BundleValidationError,
    load_bundle,
)


def _write_release(tmp_path, **changes):
    manifest = {
        "format_version": RELEASE_FORMAT_VERSION,
        "release_name": "test-release",
        "scenarios": [{"id": "steady", "label": "Steady"}],
        "source": {"type": "solver_runs", "runs": ["steady-run"]},
        "created_at": "2026-11-13T00:00:00Z",
    }
    manifest.update(changes)
    (tmp_path / "labelled").mkdir()
    pq.write_table(
        pa.table({"Scenario": ["steady"], "Value": [1.0]}),
        tmp_path / "labelled" / "energy_demand.parquet",
    )
    (tmp_path / "raw").mkdir()
    pq.write_table(
        pa.table({"Scenario": ["steady"], "Value": [1.0]}),
        tmp_path / "raw" / "raw_results.parquet",
    )
    (tmp_path / "bundle.json").write_text(json.dumps(manifest), encoding="utf-8")
    return manifest


def test_load_bundle_exposes_all_parquets_and_scenarios(tmp_path):
    _write_release(tmp_path)

    bundle = load_bundle(tmp_path)

    assert bundle.scenarios == ({"id": "steady", "label": "Steady"},)
    assert bundle.parquet_files == (
        tmp_path / "labelled" / "energy_demand.parquet",
        tmp_path / "raw" / "raw_results.parquet",
    )
    assert bundle.labelled_file("energy_demand.parquet") == (
        tmp_path / "labelled" / "energy_demand.parquet"
    )


def test_load_bundle_rejects_incompatible_version(tmp_path):
    _write_release(tmp_path, format_version=RELEASE_FORMAT_VERSION + 1)

    with pytest.raises(BundleValidationError, match="Unsupported release format version"):
        load_bundle(tmp_path)


def test_labelled_file_rejects_missing_requested_dataset(tmp_path):
    _write_release(tmp_path)
    bundle = load_bundle(tmp_path)

    with pytest.raises(BundleValidationError, match="Missing labelled dataset"):
        bundle.labelled_file("not_present.parquet")


def test_load_bundle_rejects_release_without_parquets(tmp_path):
    _write_release(tmp_path)
    for parquet_file in tmp_path.rglob("*.parquet"):
        parquet_file.unlink()

    with pytest.raises(BundleValidationError, match="contains no Parquet files"):
        load_bundle(tmp_path)
