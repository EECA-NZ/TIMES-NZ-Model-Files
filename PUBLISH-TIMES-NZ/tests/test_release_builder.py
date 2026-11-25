"""Tests for release assembly without production result data."""

from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from publish_times_nz.release_builder import (
    ReleaseBuildError,
    build_release,
    import_legacy_release,
)
from publish_times_nz.reporting import read_summary_csv


def _write_parquet(directory, filename, scenarios):
    (directory / filename).parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(
        pa.table({"Scenario": scenarios, "Value": list(range(len(scenarios)))}),
        directory / filename,
    )


def test_build_release_combines_parquets_and_summary_csvs(tmp_path):
    steady = tmp_path / "steady" / "postprocessed"
    shift = tmp_path / "shift" / "postprocessed"
    for source, scenario in ((steady, "steady"), (shift, "shift")):
        _write_parquet(source, "labelled/energy_demand.parquet", [scenario])
        _write_parquet(source, "raw_results.parquet", [scenario])
        _write_parquet(source, "labelled/future_output.parquet", [scenario])
        (source / "summaries/electricity").mkdir(parents=True)
        pd.DataFrame(
            {
                "Scenario": [scenario],
                "Period": [2030],
                "Unit": ["Share"],
                "Value": [
                    float("nan") if scenario == "steady" else 0.12345678901234568
                ],
            }
        ).to_csv(source / "summaries/electricity/energy.csv", index=False)
        (source / "metadata").mkdir()
        (source / "metadata/fuels.csv").write_text("Fuel\nCoal\n")

    bundle = build_release("comparison", [steady, shift], tmp_path / "releases")

    assert [scenario["id"] for scenario in bundle.scenarios] == ["steady", "shift"]
    assert {path.relative_to(bundle.path) for path in bundle.result_files} == {
        Path("labelled/energy_demand.parquet"),
        Path("labelled/future_output.parquet"),
        Path("summaries/electricity/energy.csv"),
        Path("raw_results.parquet"),
    }
    assert pq.read_table(bundle.labelled_file("energy_demand.parquet"))[
        "Scenario"
    ].to_pylist() == [
        "steady",
        "shift",
    ]
    summary = read_summary_csv(bundle.path / "summaries/electricity/energy.csv")
    assert summary.Scenario.tolist() == ["steady", "shift"]
    assert summary.Value.isna().tolist() == [True, False]
    assert summary.Value.iloc[1] == 0.12345678901234568


def test_build_release_rejects_duplicate_scenarios_before_publication(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    _write_parquet(first, "labelled/energy_demand.parquet", ["steady"])
    _write_parquet(second, "labelled/energy_demand.parquet", ["steady"])

    with pytest.raises(ReleaseBuildError, match="duplicate scenario IDs"):
        build_release("duplicate", [first, second], tmp_path / "releases")

    assert not (tmp_path / "releases" / "duplicate").exists()


@pytest.mark.parametrize(
    "filename",
    [
        "energy_demand.parquet",
        "raw/raw_results.parquet",
        "labelled/raw_results.parquet",
        "unexpected/topic.parquet",
        "summaries/old.parquet",
    ],
)
def test_build_release_rejects_nonstandard_layouts(tmp_path, filename):
    source = tmp_path / "old"
    _write_parquet(source, "labelled/energy_demand.parquet", ["steady"])
    _write_parquet(source, filename, ["steady"])
    with pytest.raises(ReleaseBuildError, match="Invalid result layout"):
        build_release("old", [source], tmp_path / "releases")
    assert not (tmp_path / "releases").exists()


def test_build_release_rejects_data_that_disagrees_with_definition(tmp_path):
    source = tmp_path / "steady" / "postprocessed"
    _write_parquet(source, "labelled/energy_demand.parquet", ["steady-v3.0.8"])
    definition = {
        "name": "standard",
        "scenarios": {"steady": "Steady"},
        "workspace_version": "3.0.9",
    }

    with pytest.raises(ReleaseBuildError, match="do not match bundle definition"):
        build_release(
            "v3.0.9-standard", [source], tmp_path / "releases", definition=definition
        )

    assert not (tmp_path / "releases").exists()


def test_build_release_never_overwrites_an_existing_release(tmp_path):
    source = tmp_path / "steady"
    _write_parquet(source, "labelled/energy_demand.parquet", ["steady"])
    releases_root = tmp_path / "releases"
    build_release("steady", [source], releases_root)

    with pytest.raises(ReleaseBuildError, match="Release already exists"):
        build_release("steady", [source], releases_root)

    assert (releases_root / "steady" / "labelled" / "energy_demand.parquet").is_file()


@pytest.mark.parametrize("prefix", ["", "labelled/"])
def test_import_legacy_release_copies_every_parquet(tmp_path, prefix):
    source = tmp_path / "legacy"
    _write_parquet(source, f"{prefix}energy_demand.parquet", ["steady", "shift"])
    _write_parquet(source, f"{prefix}custom_topic.parquet", ["steady", "shift"])
    _write_parquet(source, "raw_results.parquet", ["steady", "shift"])
    (source / "summaries").mkdir()
    pd.DataFrame({"Scenario": ["steady", "shift"], "Value": [1.2, 3.4]}).to_csv(
        source / "summaries/energy.csv", index=False
    )

    bundle = import_legacy_release("v308", source, tmp_path / "releases", "v308")

    assert [scenario["id"] for scenario in bundle.scenarios] == ["shift", "steady"]
    assert {path.relative_to(bundle.path) for path in bundle.parquet_files} == {
        Path("raw_results.parquet"),
        Path("labelled/custom_topic.parquet"),
        Path("labelled/energy_demand.parquet"),
    }
    assert bundle.manifest["source"] == {"type": "legacy", "legacy_source": "v308"}
    assert read_summary_csv(bundle.path / "summaries/energy.csv").Value.tolist() == [
        1.2,
        3.4,
    ]


def test_build_release_checks_scenario_ids_in_summary_csvs(tmp_path):
    source = tmp_path / "steady"
    _write_parquet(source, "labelled/energy_demand.parquet", ["steady"])
    (source / "summaries").mkdir()
    (source / "summaries/energy.csv").write_text("Scenario,Value\nshift,1.2\n")
    with pytest.raises(ReleaseBuildError, match="one scenario"):
        build_release("invalid", [source], tmp_path / "releases")
    assert not (tmp_path / "releases").exists()


def test_import_legacy_release_moves_old_raw_results_to_root(tmp_path):
    source = tmp_path / "legacy"
    _write_parquet(source, "labelled/energy_demand.parquet", ["steady"])
    _write_parquet(source, "raw/raw_results.parquet", ["steady"])

    bundle = import_legacy_release("old", source, tmp_path / "releases")

    assert (bundle.path / "raw_results.parquet").is_file()
    assert not (bundle.path / "raw").exists()

    _write_parquet(source, "raw_results.parquet", ["steady"])
    with pytest.raises(ReleaseBuildError, match="Duplicate legacy dataset"):
        import_legacy_release("both", source, tmp_path / "releases")


def test_import_legacy_release_rejects_duplicate_dataset_paths(tmp_path):
    source = tmp_path / "legacy"
    _write_parquet(source, "energy_demand.parquet", ["steady"])
    _write_parquet(source, "labelled/energy_demand.parquet", ["steady"])

    with pytest.raises(ReleaseBuildError, match="Duplicate legacy dataset"):
        import_legacy_release("legacy", source, tmp_path / "releases")
    assert not (tmp_path / "releases").exists()
