"""Tests for the Explorer's tracked release selection."""

import json

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from publish_times_nz import app_config
from publish_times_nz.app_config import configured_release_path
from publish_times_nz.release_bundle import RELEASE_FORMAT_VERSION


def test_configured_bundle_uses_root_config(tmp_path, monkeypatch):
    (tmp_path / "explorer_bundle.toml").write_text(
        'release = "selected"\n', encoding="utf-8"
    )
    bundle_path = tmp_path / "releases" / "selected"
    (bundle_path / "labelled").mkdir(parents=True)
    pq.write_table(
        pa.table({"Scenario": ["steady"], "Value": [1.0]}),
        bundle_path / "labelled" / "energy_demand.parquet",
    )
    (bundle_path / "release-manifest.json").write_text(
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
    monkeypatch.setattr(app_config, "PUBLISH_ROOT", tmp_path)
    app_config.configured_bundle.cache_clear()

    assert app_config.configured_bundle().path == bundle_path

    app_config.configured_bundle.cache_clear()


@pytest.mark.parametrize("value", ['"../outside"', '"/absolute"', '".."', '""', "42"])
def test_release_config_rejects_invalid_folder_names(tmp_path, value):
    (tmp_path / "explorer_bundle.toml").write_text(
        f"release = {value}\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="folder name under releases"):
        configured_release_path(tmp_path)
