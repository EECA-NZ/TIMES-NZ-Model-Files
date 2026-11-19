"""Bundle selection uses synthetic manifests and Parquets, never local solves."""

import json
import sys
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from publish_times_nz import cli
from publish_times_nz.bundle_definition import (
    build_bundle,
    load_definition,
    select_runs,
)
from publish_times_nz.release_builder import ReleaseBuildError


def _manifest(case="steady", version="3.0.9", day=1):
    return {
        "case_name": case,
        "scenario_name": f"{case}-v{version}",
        "execution": {
            "status": "completed",
            "completed_at": f"2026-11-{day:02}T12:00:00+00:00",
        },
        "postprocessing": {"status": "completed", "files": ["energy_demand.parquet"]},
    }


def test_select_runs_uses_manifest_time_and_preserves_case_order():
    runs = {
        Path("steady-old"): _manifest(day=1),
        Path("steady-new"): _manifest(day=2),
        Path("other-version"): _manifest(version="3.0.8", day=3),
        Path("shift"): _manifest(case="shift"),
        Path("failed"): {**_manifest(day=4), "execution": {"status": "gams_failed"}},
        Path("partial"): {**_manifest(day=5), "postprocessing": {"status": "running"}},
        Path("legacy"): {
            key: value
            for key, value in _manifest(day=6).items()
            if key != "postprocessing"
        },
    }

    assert select_runs(["shift", "steady"], "3.0.9", runs) == [
        Path("shift"),
        Path("steady-new"),
    ]


def test_select_runs_rejects_missing_case_and_ambiguous_latest_run():
    with pytest.raises(ReleaseBuildError, match="No completed.*shift-v3.0.9"):
        select_runs(["steady", "shift"], "3.0.9", {Path("steady"): _manifest()})
    with pytest.raises(ReleaseBuildError, match="Multiple runs"):
        select_runs(
            ["steady"], "3.0.9", {Path("a"): _manifest(), Path("b"): _manifest()}
        )


@pytest.mark.parametrize("completed_at", ["invalid", "2026-11-01T12:00:00", None])
def test_select_runs_rejects_invalid_completion_time(completed_at):
    manifest = _manifest()
    manifest["execution"]["completed_at"] = completed_at
    with pytest.raises(ReleaseBuildError, match="Invalid solve completion timestamp"):
        select_runs(["steady"], "3.0.9", {Path("run"): manifest})


@pytest.mark.parametrize(
    "contents",
    [
        'name = "standard"\nscenarios = []',
        'name = "standard"\nscenarios = ["steady", "steady"]',
        'name = "standard"\nscenarios = {}',
        'name = "standard"\nscenarios = {steady = ""}',
        'name = "standard"\nscenarios = {steady = " "}',
        'name = "standard"\nscenarios = {steady = 42}',
        'name = "standard"\nscenarios = {" " = "Steady"}',
        'name = "../escape"\nscenarios = {steady = "Steady"}',
        'name = "standard"\nscenarios = {steady = "Steady"}\nunknown = true',
    ],
)
def test_load_definition_rejects_invalid_recipe(tmp_path, contents):
    path = tmp_path / "bundle.toml"
    path.write_text(contents, encoding="utf-8")
    with pytest.raises(ReleaseBuildError):
        load_definition(path)


def test_build_bundle_records_recipe_and_combines_partial_topics(tmp_path, capsys):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nversion = "3.0.9"\n', encoding="utf-8"
    )
    definition = tmp_path / "standard.toml"
    definition.write_text(
        'name = "standard"\n[scenarios]\nsteady = "Steady"\nshift = "Shift"\n',
        encoding="utf-8",
    )
    for case in ("steady", "shift"):
        run = tmp_path / "SOLVE-TIMES-NZ" / "build" / "solves" / f"{case}-local-run"
        output = run / "postprocessed"
        output.mkdir(parents=True)
        manifest = _manifest(case=case)
        (run / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        table = pa.table({"Scenario": [manifest["scenario_name"]], "Value": [1.0]})
        pq.write_table(table, output / "energy_demand.parquet")
        if case == "shift":
            pq.write_table(table, output / "sensitivity_only.parquet")

    bundle = build_bundle(definition, tmp_path, tmp_path / "releases")

    assert bundle.path.name == "v3.0.9-standard"
    assert bundle.manifest["source"] == {
        "type": "solver_runs",
        "runs": ["steady-local-run", "shift-local-run"],
        "definition": {
            "name": "standard",
            "scenarios": {"steady": "Steady", "shift": "Shift"},
            "workspace_version": "3.0.9",
        },
    }
    assert bundle.scenarios == (
        {"id": "steady-v3.0.9", "label": "Steady"},
        {"id": "shift-v3.0.9", "label": "Shift"},
    )
    assert pq.read_table(bundle.labelled_file("energy_demand.parquet"))[
        "Scenario"
    ].to_pylist() == ["steady-v3.0.9", "shift-v3.0.9"]
    assert pq.read_table(bundle.labelled_file("sensitivity_only.parquet"))[
        "Scenario"
    ].to_pylist() == ["shift-v3.0.9"]
    assert "steady-local-run" in capsys.readouterr().out

    (output / "energy_demand.parquet").unlink()
    with pytest.raises(ReleaseBuildError, match="outputs are missing"):
        build_bundle(definition, tmp_path, tmp_path / "other-releases")
    assert not (tmp_path / "other-releases").exists()


def test_build_bundle_cli_reports_missing_run_without_traceback(
    tmp_path, monkeypatch, capsys
):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nversion = "3.0.9"\n', encoding="utf-8"
    )
    definition = tmp_path / "standard.toml"
    definition.write_text(
        'name = "standard"\n[scenarios]\nsteady = "Steady"\n', encoding="utf-8"
    )
    monkeypatch.setattr(
        cli, "DEFAULT_RELEASES_ROOT", tmp_path / "PUBLISH-TIMES-NZ" / "releases"
    )
    monkeypatch.setattr(
        sys, "argv", ["publish-times-nz", "build-release", str(definition)]
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    assert error.value.code == 2
    assert (
        "No completed, postprocessed run for steady-v3.0.9" in capsys.readouterr().err
    )
