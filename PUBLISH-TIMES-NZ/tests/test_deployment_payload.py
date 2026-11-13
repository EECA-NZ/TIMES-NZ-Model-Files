"""Tests for the curated rsconnect payload."""

import json

import pyarrow as pa
import pyarrow.parquet as pq

from publish_times_nz.deployment_payload import prepare_deployment_payload
from publish_times_nz.release_bundle import RELEASE_FORMAT_VERSION


def test_prepare_deployment_payload_copies_only_selected_release(tmp_path, monkeypatch):
    for name in ("src", "assets", "www"):
        (tmp_path / name).mkdir()
    (tmp_path / "app.py").touch()
    (tmp_path / ".env").touch()
    release = tmp_path / "releases" / "v308"
    (release / "labelled").mkdir(parents=True)
    pq.write_table(pa.table({"Scenario": ["steady"]}), release / "labelled" / "data.parquet")
    (release / "bundle.json").write_text(
        json.dumps({"format_version": RELEASE_FORMAT_VERSION, "release_name": "v308", "scenarios": [{"id": "steady", "label": "steady"}], "source": {"type": "legacy", "legacy_source": "test"}, "created_at": "2026-11-13T00:00:00Z"}),
        encoding="utf-8",
    )
    (tmp_path / "releases" / "other").mkdir()

    monkeypatch.setattr(
        "publish_times_nz.deployment_payload._write_requirements",
        lambda _, destination: destination.touch(),
    )
    deploy_path = prepare_deployment_payload(tmp_path)

    assert (deploy_path / ".env").is_file()
    assert (deploy_path / "requirements.txt").is_file()
    assert (deploy_path / "releases" / "v308" / "bundle.json").is_file()
    assert not (deploy_path / "releases" / "other").exists()
