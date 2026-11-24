"""Publication exports copy prepared values and keep source releases intact."""

import io
import json
import zipfile

import pandas as pd
import pytest

from publish_times_nz.cli import main
from publish_times_nz.release_bundle import ReleaseBundle
from publish_times_nz.reporting import export_summaries, read_summary_csv
from publish_times_nz.utilities.output_packaging import build_outputs_zip_bytes


def bundle(root):
    (root / "summaries").mkdir(parents=True)
    pd.DataFrame(
        {
            "Scenario": ["s", "t"],
            "Period": [2030, 2030],
            "Unit": ["PJ", "PJ"],
            "Value": [1.2, 3.4],
        }
    ).to_csv(root / "summaries/demand.csv", index=False)
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
    before = (source.path / "summaries/demand.csv").read_bytes()
    output = tmp_path / "exports"
    paths = export_summaries(source, output, ["t"])
    assert paths == [output / "demand.csv"]
    assert pd.read_csv(paths[0]).to_dict("records") == [
        {"Scenario": "Shift", "Period": 2030, "Unit": "PJ", "Value": 3.4}
    ]
    assert json.loads((output / "summary-export-manifest.json").read_text())[
        "scenario_ids"
    ] == ["t"]
    assert (source.path / "summaries/demand.csv").read_bytes() == before


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
    pd.DataFrame({"Scenario": ["s", "t"], "PV": [1.2, 3.4]}).to_parquet(
        source.path / "raw_results.parquet", index=False
    )
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


def test_summary_csv_preserves_precision_text_and_undefined_values(tmp_path):
    source = tmp_path / "summary.csv"
    frame = pd.DataFrame(
        {
            "Scenario": ["001", "NA"],
            "Period": [2030, 2040],
            "Fuel": ["NA", "001"],
            "Unit": ["Share", "Share"],
            "Value": [0.12345678901234568, float("nan")],
        }
    )
    frame.to_csv(source, index=False)
    pd.testing.assert_frame_equal(read_summary_csv(source), frame)


@pytest.mark.parametrize(
    "contents",
    [
        "Scenario,Value\ns,invalid\n",
        "Scenario,Period,Value\ns,2030.5,1\n",
        "Scenario,Value\n,1\n",
        "Scenario,Value\ns,inf\n",
        "Scenario,Period\ns,2030\n",
    ],
)
def test_summary_csv_rejects_invalid_fields(tmp_path, contents):
    source = tmp_path / "summary.csv"
    source.write_text(contents)
    with pytest.raises(ValueError):
        read_summary_csv(source)


def test_full_results_download_includes_summary_csvs_without_name_collisions(
    tmp_path, monkeypatch
):
    source = bundle(tmp_path / "release")
    (source.path / "labelled").mkdir()
    pd.DataFrame({"Scenario": ["s"], "Value": [9.0]}).to_parquet(
        source.path / "labelled/demand.parquet", index=False
    )
    monkeypatch.setattr(
        "publish_times_nz.utilities.value_mappings.load_column_value_mappings",
        lambda: {"Scenario": {"s": "Steady", "t": "Shift"}},
    )
    with zipfile.ZipFile(
        io.BytesIO(build_outputs_zip_bytes(source.result_files))
    ) as archive:
        assert set(archive.namelist()) == {"demand.csv", "summaries/demand.csv"}
        summary = pd.read_csv(io.BytesIO(archive.read("summaries/demand.csv")))
    assert summary.Scenario.tolist() == ["Steady", "Shift"]
    assert summary.Value.tolist() == [1.2, 3.4]
