"""Publication exports copy prepared values and keep source releases intact."""

import json

import pandas as pd
import pytest

from publish_times_nz.cli import main
from publish_times_nz.release_bundle import ReleaseBundle
from publish_times_nz.reporting import export_summaries


def bundle(root):
    (root / "summaries").mkdir(parents=True)
    pd.DataFrame(
        {
            "Scenario": ["s", "t"],
            "Period": [2030, 2030],
            "Unit": ["PJ", "PJ"],
            "Value": [1.2, 3.4],
        }
    ).to_parquet(root / "summaries/demand.parquet", index=False)
    return ReleaseBundle(
        root,
        {
            "format_version": 1,
            "release_name": "example",
            "source": {"type": "legacy", "legacy_source": "synthetic"},
            "created_at": "2026-11-24T00:00:00Z",
            "scenarios": [
                {"id": "s", "label": "Steady"},
                {"id": "t", "label": "Shift"},
            ],
        },
    )


def test_export_summaries_selects_and_labels_without_changing_values(tmp_path):
    source = bundle(tmp_path / "release")
    before = (source.path / "summaries/demand.parquet").read_bytes()
    output = tmp_path / "exports"
    paths = export_summaries(source, output, ["t"])
    assert paths == [output / "demand.csv"]
    assert pd.read_csv(paths[0]).to_dict("records") == [
        {"Scenario": "Shift", "Period": 2030, "Unit": "PJ", "Value": 3.4}
    ]
    assert json.loads((output / "summary-export-manifest.json").read_text())[
        "scenario_ids"
    ] == ["t"]
    assert (source.path / "summaries/demand.parquet").read_bytes() == before


def test_export_summaries_rejects_unknown_selections_and_writes_inside_release(
    tmp_path,
):
    source = bundle(tmp_path / "release")
    with pytest.raises(ValueError, match="scenario IDs"):
        export_summaries(source, tmp_path / "out", ["missing"])
    with pytest.raises(ValueError, match="outside the source release"):
        export_summaries(source, source.path / "exports")
    assert not (tmp_path / "out").exists()


def test_export_summaries_command_uses_only_the_selected_release(
    tmp_path, monkeypatch, capsys
):
    source = bundle(tmp_path / "release")
    (source.path / "release-manifest.json").write_text(json.dumps(source.manifest))
    monkeypatch.setattr(
        "sys.argv",
        [
            "publish-times-nz",
            "export-summaries",
            "release",
            "--releases-root",
            str(tmp_path),
            "--output",
            str(tmp_path / "exports"),
            "--scenario",
            "s",
        ],
    )
    main()
    assert "Exported 1 summaries" in capsys.readouterr().out
    assert pd.read_csv(tmp_path / "exports/demand.csv").Scenario.tolist() == ["Steady"]
