"""Tests for the Explorer's tracked release selection."""

import json

import pyarrow as pa
import pyarrow.parquet as pq

from publish_times_nz.app import release
from publish_times_nz.release_bundle import RELEASE_FORMAT_VERSION


def test_configured_bundle_uses_tracked_release_path(tmp_path, monkeypatch):
    (tmp_path / "labelled").mkdir()
    pq.write_table(
        pa.table({"Scenario": ["steady"], "Value": [1.0]}),
        tmp_path / "labelled" / "energy_demand.parquet",
    )
    (tmp_path / "bundle.json").write_text(
        json.dumps(
            {
                "format_version": RELEASE_FORMAT_VERSION,
                "release_name": "test",
                "scenarios": [{"id": "steady", "label": "Steady"}],
                "source": {"type": "legacy", "legacy_source": "test"},
                "created_at": "2026-11-13T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(release, "RELEASE_PATH", tmp_path)
    release.configured_bundle.cache_clear()

    assert release.configured_bundle().path == tmp_path

    release.configured_bundle.cache_clear()
