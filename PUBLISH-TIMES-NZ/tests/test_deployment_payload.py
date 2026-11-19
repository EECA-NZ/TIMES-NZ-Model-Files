"""Tests for the curated rsconnect payload."""

import json

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from publish_times_nz.app_config import configured_release_path, load_explorer_config
from publish_times_nz.deployment_payload import prepare_deployment_payload
from publish_times_nz.release_bundle import RELEASE_FORMAT_VERSION


@pytest.mark.parametrize("override", [None, "override"])
def test_prepare_deployment_payload_copies_only_selected_release(
    tmp_path, monkeypatch, override
):
    (tmp_path / ".python-version").write_text("3.12\n", encoding="utf-8")
    tmp_path = tmp_path / "PUBLISH-TIMES-NZ"
    tmp_path.mkdir()
    for name in ("src", "assets", "www"):
        (tmp_path / name).mkdir()
    (tmp_path / "app.py").touch()
    (tmp_path / ".env").touch()
    config_text = (
        'release = "configured"\n[column_value_mappings.Scenario]\nsteady = "Steady"\n'
        '[column_value_mappings.Region]\nNI = "Te Ika-a-Māui"\n'
    )
    (tmp_path / "explorer_bundle.toml").write_text(config_text, encoding="utf-8")
    selected = override or "configured"
    release = tmp_path / "releases" / selected
    (release / "labelled").mkdir(parents=True)
    pq.write_table(
        pa.table({"Scenario": ["steady"]}), release / "labelled" / "data.parquet"
    )
    (release / "release-manifest.json").write_text(
        json.dumps(
            {
                "format_version": RELEASE_FORMAT_VERSION,
                "release_name": selected,
                "scenarios": [{"id": "steady", "label": "steady"}],
                "source": {"type": "legacy", "legacy_source": "test"},
                "created_at": "2026-11-13T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "releases" / "other").mkdir()

    monkeypatch.setattr(
        "publish_times_nz.deployment_payload._write_requirements",
        lambda _, destination: destination.touch(),
    )
    deploy_path = prepare_deployment_payload(tmp_path, override)

    assert (deploy_path / ".env").is_file()
    assert (deploy_path / ".python-version").read_text(encoding="utf-8") == "3.12\n"
    assert (deploy_path / "requirements.txt").is_file()
    assert configured_release_path(deploy_path) == deploy_path / "releases" / selected
    assert (configured_release_path(deploy_path) / "release-manifest.json").is_file()
    assert not (deploy_path / "releases" / "other").exists()
    assert load_explorer_config(deploy_path) == {
        "release": selected,
        "column_value_mappings": {
            "Scenario": {"steady": "Steady"},
            "Region": {"NI": "Te Ika-a-Māui"},
        },
    }
    assert (tmp_path / "explorer_bundle.toml").read_text() == config_text
