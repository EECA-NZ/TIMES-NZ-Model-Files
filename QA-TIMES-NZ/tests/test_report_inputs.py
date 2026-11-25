"""Input selection uses synthetic manifests and summaries, never local results."""

import json

import pandas as pd
import pytest

from qa_times_nz import report_inputs

SUMMARY = "summaries/electricity/electricity_generation.csv"


@pytest.fixture
def repository(tmp_path, monkeypatch):
    monkeypatch.setattr(report_inputs, "REPOSITORY_ROOT", tmp_path)
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "3.0.9"\n')
    (tmp_path / "QA-TIMES-NZ").mkdir()
    return tmp_path


def write_summary(root, scenarios, values):
    path = root / SUMMARY
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            "Scenario": scenarios,
            "Period": [2030] * len(scenarios),
            "Unit": ["TWh"] * len(scenarios),
            "Value": values,
        }
    ).to_csv(path, index=False)


def write_release(repository):
    root = repository / "PUBLISH-TIMES-NZ/releases/v308"
    write_summary(root, ["steady-v308", "shift-v308"], [1.25, 9.5])
    pd.DataFrame({"Scenario": ["steady-v308", "shift-v308"]}).to_parquet(
        root / "raw_results.parquet", index=False
    )
    (root / "release-manifest.json").write_text(
        json.dumps(
            {
                "format_version": 1,
                "release_name": "v308",
                "source": {"type": "legacy", "legacy_source": "synthetic"},
                "created_at": "2026-11-24T00:00:00Z",
                "scenarios": [
                    {"id": "steady-v308", "label": "Steady"},
                    {"id": "shift-v308", "label": "Shift"},
                ],
            }
        )
    )
    return {"source": "RELEASE", "release": "v308", "scenario": "steady-v308"}


def write_run(
    repository,
    *,
    case="steady",
    version="3.0.9",
    stamp="20261124T010000Z",
    day=24,
    value=2.5,
):
    run = repository / "SOLVE-TIMES-NZ/build/solves" / f"{case}-v{version}-{stamp}"
    scenario = f"{case}-v{version}"
    write_summary(run / "postprocessed", [scenario], [value])
    (run / "manifest.json").write_text(
        json.dumps(
            {
                "case_name": case,
                "scenario_name": scenario,
                "execution": {
                    "status": "completed",
                    "completed_at": f"2026-11-{day:02}T02:00:00Z",
                },
                "postprocessing": {"status": "completed", "files": [SUMMARY]},
            }
        )
    )
    return run


def change_manifest(run, **updates):
    path = run / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest.update(updates)
    path.write_text(json.dumps(manifest))


def write_config(repository, baseline, candidate, *, dev=False, tolerance="0.05"):
    name = "report_config_dev.toml" if dev else "report_config.toml"
    contents = f"tolerance = {tolerance}\n"
    for role, selection in [("baseline", baseline), ("candidate", candidate)]:
        contents += f"\n[{role}]\n"
        for key, value in selection.items():
            contents += f"{key} = {json.dumps(value)}\n"
    path = repository / "QA-TIMES-NZ" / name
    path.write_text(contents)
    return path


@pytest.mark.parametrize("baseline_source", ["RELEASE", "SOLVE"])
@pytest.mark.parametrize("candidate_source", ["RELEASE", "SOLVE"])
def test_all_source_pairs_resolve_and_read_prepared_values(
    repository, capsys, baseline_source, candidate_source
):
    release = write_release(repository)
    run = write_run(repository)
    selectors = {"RELEASE": release, "SOLVE": {"source": "SOLVE", "scenario": "steady"}}
    write_config(repository, selectors[baseline_source], selectors[candidate_source])
    comparison = report_inputs.resolve_inputs()
    assert comparison["tolerance"] == 0.05
    for role, source in [
        ("baseline", baseline_source),
        ("candidate", candidate_source),
    ]:
        selected = comparison[role]
        frame = report_inputs.load_summary(selected, SUMMARY)
        assert frame.Value.item() == (1.25 if source == "RELEASE" else 2.5)
        assert frame.Scenario.tolist() == [selected["scenario"]]
        assert frame.Period.dtype == "int64"
        assert selected["manifest_path"].is_file()
        assert selected["manifest"]
        assert selected["workspace_version"] == "3.0.9"
        if source == "SOLVE":
            assert selected["result_root"] == run / "postprocessed"
            assert selected["timestamp"] == "20261124T010000Z"
        else:
            assert selected["label"] == "Steady"
    output = capsys.readouterr().out
    assert "baseline:" in output and "candidate:" in output
    assert "workspace=3.0.9" in output


def test_latest_matches_publish_policy_and_pin_uses_directory_timestamp(repository):
    write_run(repository, stamp="20261124T010000Z", day=23)
    latest = write_run(repository, stamp="20261120T010000Z", day=24)
    old = write_run(repository, version="3.0.8", stamp="20261125T010000Z", day=25)
    incomplete = write_run(repository, stamp="20261126T010000Z", day=26)
    change_manifest(incomplete, postprocessing={"status": "running"})
    selected = report_inputs.resolve_input({"source": "SOLVE", "scenario": "steady"})
    assert selected["result_root"] == latest / "postprocessed"
    assert selected["timestamp"] == "20261120T010000Z"
    pinned = report_inputs.resolve_input(
        {"source": "SOLVE", "scenario": "steady", "timestamp": "20261125T010000Z"}
    )
    assert pinned["result_root"] == old / "postprocessed"
    assert pinned["version"] == "3.0.8"
    assert pinned["workspace_version"] == "3.0.9"


@pytest.mark.parametrize("status_field", ["execution", "postprocessing"])
def test_pinned_incomplete_run_is_rejected_without_fallback(repository, status_field):
    write_run(repository)
    pinned = write_run(repository, stamp="20261125T010000Z", day=25)
    change_manifest(pinned, **{status_field: {"status": "running"}})
    with pytest.raises(ValueError, match="No completed"):
        report_inputs.resolve_input(
            {"source": "SOLVE", "scenario": "steady", "timestamp": "20261125T010000Z"}
        )


def test_rejects_missing_and_ambiguous_pins_and_latest_ties(repository):
    write_run(repository)
    write_run(repository, stamp="20261123T010000Z")
    selection = {"source": "SOLVE", "scenario": "steady"}
    with pytest.raises(ValueError, match="Multiple runs"):
        report_inputs.resolve_input(selection)
    with pytest.raises(ValueError, match="found 0"):
        report_inputs.resolve_input({**selection, "timestamp": "20261122T010000Z"})
    write_run(repository, version="3.0.8")
    with pytest.raises(ValueError, match="found 2"):
        report_inputs.resolve_input({**selection, "timestamp": "20261124T010000Z"})


def test_unpinned_selection_never_substitutes_an_old_version(repository):
    write_run(repository, version="3.0.8")
    with pytest.raises(ValueError, match="No completed.*steady-v3.0.9"):
        report_inputs.resolve_input({"source": "SOLVE", "scenario": "steady"})


@pytest.mark.parametrize(
    "files", [[], [SUMMARY, "labelled/missing.parquet"], ["../outside.csv"]]
)
def test_completed_run_requires_valid_existing_declared_outputs(repository, files):
    run = write_run(repository)
    change_manifest(run, postprocessing={"status": "completed", "files": files})
    with pytest.raises(ValueError):
        report_inputs.resolve_input({"source": "SOLVE", "scenario": "steady"})


def test_main_dev_selection_is_explicit_and_missing_dev_does_not_fall_back(repository):
    release = write_release(repository)
    write_config(repository, release, release)
    assert report_inputs.load_config()["tolerance"] == 0.05
    with pytest.raises(FileNotFoundError, match="report_config_dev.toml"):
        report_inputs.load_config(dev=True)
    write_config(repository, release, release, dev=True, tolerance="0.1")
    assert report_inputs.load_config(dev=True)["tolerance"] == 0.1
    assert report_inputs.load_config()["tolerance"] == 0.05


@pytest.mark.parametrize("tolerance", ["-0.1", "nan", "inf", "true", '"0.05"'])
def test_config_rejects_invalid_tolerance(repository, tolerance):
    release = write_release(repository)
    write_config(repository, release, release, tolerance=tolerance)
    with pytest.raises(ValueError, match="tolerance"):
        report_inputs.load_config()


@pytest.mark.parametrize(
    "selection",
    [
        {"source": "OTHER", "scenario": "steady"},
        {"source": [], "scenario": "steady"},
        {"source": "RELEASE", "scenario": "steady"},
        {
            "source": "RELEASE",
            "release": "v308",
            "scenario": "steady",
            "timestamp": "20261124T010000Z",
        },
        {"source": "SOLVE", "scenario": "steady", "release": "v308"},
        {"source": "SOLVE", "scenario": "../steady"},
        {"source": "SOLVE", "scenario": "steady", "label": " "},
        {"source": "SOLVE", "scenario": "steady", "timestamp": "20260230T010000Z"},
        {"source": "SOLVE", "scenario": "steady", "timestamp": "2026-11-24"},
    ],
)
def test_config_rejects_invalid_source_selectors(repository, selection):
    write_config(repository, selection, {"source": "SOLVE", "scenario": "steady"})
    with pytest.raises(ValueError):
        report_inputs.load_config()


def test_release_validation_is_reused_and_unknown_scenarios_are_rejected(repository):
    selection = write_release(repository)
    with pytest.raises(ValueError, match="absent"):
        report_inputs.resolve_input({**selection, "scenario": "missing"})
    path = repository / "PUBLISH-TIMES-NZ/releases/v308/release-manifest.json"
    manifest = json.loads(path.read_text())
    manifest["format_version"] = 999
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="Unsupported release format"):
        report_inputs.resolve_input(selection)


def test_release_definition_metadata_must_be_a_table(repository):
    selection = write_release(repository)
    path = repository / "PUBLISH-TIMES-NZ/releases/v308/release-manifest.json"
    manifest = json.loads(path.read_text())
    manifest["source"]["definition"] = []
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="Invalid release definition metadata"):
        report_inputs.resolve_input(selection)


def test_reader_preserves_nulls_and_absence_and_rejects_unknown_scenarios(repository):
    run = write_run(repository, value=float("nan"))
    selected = report_inputs.resolve_input({"source": "SOLVE", "scenario": "steady"})
    assert report_inputs.load_summary(selected, SUMMARY).Value.isna().all()
    assert (
        report_inputs.load_summary(selected, "summaries/electricity/battery_flows.csv")
        is None
    )
    write_summary(run / "postprocessed", ["other-scenario"], [1])
    with pytest.raises(ValueError, match="Undeclared"):
        report_inputs.load_summary(selected, SUMMARY)


@pytest.mark.parametrize(
    "path", ["../outside.csv", "/tmp/outside.csv", "labelled/energy.parquet"]
)
def test_reader_rejects_non_summary_paths(repository, path):
    write_run(repository)
    selected = report_inputs.resolve_input({"source": "SOLVE", "scenario": "steady"})
    with pytest.raises(ValueError):
        report_inputs.load_summary(selected, path)


def test_same_scenario_id_in_different_runs_keeps_baseline_and_candidate_separate(
    repository,
):
    write_run(repository, stamp="20261123T010000Z", day=23, value=1.0)
    write_run(repository, value=2.0)
    selection = {"source": "SOLVE", "scenario": "steady"}
    write_config(repository, {**selection, "timestamp": "20261123T010000Z"}, selection)
    comparison = report_inputs.resolve_inputs()
    assert comparison["baseline"]["scenario"] == comparison["candidate"]["scenario"]
    assert report_inputs.load_summary(comparison["baseline"], SUMMARY).Value.item() == 1
    assert (
        report_inputs.load_summary(comparison["candidate"], SUMMARY).Value.item() == 2
    )


@pytest.mark.parametrize(
    "contents",
    [
        "tolerance = 0.05\nbaseline = 1\ncandidate = {}\n",
        'tolerance = 0.05\n[baseline]\nsource = "SOLVE"\nscenario = "steady"\n',
        'unknown = true\ntolerance = 0.05\n[baseline]\nsource = "SOLVE"\nscenario = "steady"\n[candidate]\nsource = "SOLVE"\nscenario = "steady"\n',
    ],
)
def test_config_rejects_missing_unknown_and_malformed_fields(repository, contents):
    (repository / "QA-TIMES-NZ/report_config.toml").write_text(contents)
    with pytest.raises(ValueError):
        report_inputs.load_config()


@pytest.mark.parametrize("contents", ["{invalid", "[]", '{"execution": []}'])
def test_malformed_solve_manifests_are_input_errors(repository, contents):
    run = write_run(repository)
    (run / "manifest.json").write_text(contents)
    with pytest.raises(ValueError, match="Invalid SOLVE manifest"):
        report_inputs.resolve_input({"source": "SOLVE", "scenario": "steady"})


def test_release_without_prepared_summaries_is_rejected(repository):
    selection = write_release(repository)
    root = repository / "PUBLISH-TIMES-NZ/releases/v308"
    (root / SUMMARY).unlink()
    with pytest.raises(ValueError, match="No prepared summary CSVs"):
        report_inputs.resolve_input(selection)


def test_reader_distinguishes_absent_scenario_rows_from_missing_declared_file(
    repository,
):
    selection = write_release(repository)
    root = repository / "PUBLISH-TIMES-NZ/releases/v308"
    write_summary(root, ["shift-v308"], [1.0])
    selected = report_inputs.resolve_input(selection)
    assert report_inputs.load_summary(selected, SUMMARY) is None
    (root / SUMMARY).unlink()
    with pytest.raises(FileNotFoundError):
        report_inputs.load_summary(selected, SUMMARY)


def test_reader_uses_declared_solve_outputs_and_keeps_whole_run_objectives(repository):
    run = write_run(repository)
    relative = "summaries/indicators/objective_function.csv"
    path = run / "postprocessed" / relative
    path.parent.mkdir()
    path.write_text("Scenario,Unit,Value\nsteady-v3.0.9,NZDb,1.25\n")
    selection = {"source": "SOLVE", "scenario": "steady", "label": "Development"}
    selected = report_inputs.resolve_input(selection)
    assert report_inputs.load_summary(selected, relative) is None
    change_manifest(
        run, postprocessing={"status": "completed", "files": [SUMMARY, relative]}
    )
    selected = report_inputs.resolve_input(selection)
    assert selected["label"] == "Development"
    objective = report_inputs.load_summary(selected, relative)
    assert "Period" not in objective
    assert objective.Value.item() == 1.25
