"""Prepared metric validation, comparisons and offline report output use fake data."""

import json

import pandas as pd
import pytest

from publish_times_nz.release_builder import build_release
from qa_times_nz import cli, report_inputs
from qa_times_nz.report import build_report
from qa_times_nz.report.build import comparisons_path
from qa_times_nz.report.charts import chart_figure, detail_chart
from qa_times_nz.report.compare import (
    different_period_spans,
    period_comparison,
    read_metric,
)
from qa_times_nz.report.render import comparison_accordion, nz_timestamp


def annual(values, unit="PJ", **groups):
    return pd.DataFrame(
        {
            "Period": [2030] * len(values),
            "Unit": [unit] * len(values),
            "Value": values,
            **groups,
        }
    )


REPORT_NAME = "TIMES-QA-Published _old_ vs Development.html"
COMPARISONS_NAME = "TIMES-QA-Published _old_ vs Development comparisons.csv"


@pytest.fixture
def repository(tmp_path, monkeypatch):
    monkeypatch.setattr(report_inputs, "REPOSITORY_ROOT", tmp_path)
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "3.0.9"\n')
    qa = tmp_path / "QA-TIMES-NZ"
    qa.mkdir()
    (qa / "report_config.toml").write_text("""tolerance = 0.05
[baseline]
source = "RELEASE"
release = "v308"
scenario = "steady-v308"
label = "Published <old>"
[candidate]
source = "SOLVE"
scenario = "steady"
label = "Development"
""")
    data = {
        "electricity/electricity_demand": annual([10], "TWh"),
        "electricity/electricity_demand_by_sector_group": annual(
            [2], "TWh", SectorGroup=["Industry"]
        ),
        "electricity/electricity_generation": annual([100], "TWh"),
        "demand/energy_demand_by_fuel": annual(
            [1, 2, 3], Fuel=["Natural gas", "Diesel", "Petrol"]
        ),
        "demand/energy_demand_by_fuel_and_sector_group": annual(
            [1, 2, 3],
            Fuel=["Natural gas", "Diesel", "Petrol"],
            SectorGroup=["Industry"] * 3,
        ),
        "demand/woody_biomass_demand": annual([3]),
        "demand/woody_biomass_demand_by_sector_group": annual(
            [3], SectorGroup=["Industry"]
        ),
        "emissions/emissions": annual([5], "Mt CO2e"),
        "emissions/emissions_by_sector_group": annual(
            [5], "Mt CO2e", SectorGroup=["Industry"]
        ),
        "indicators/objective_function": pd.DataFrame(
            {"Unit": ["NZDb"], "Value": [10.0]}
        ),
        "indicators/renewable_generation_share": annual([0.63, 63]).assign(
            Unit=["Share", "%"]
        ),
        "indicators/renewable_tfec_share": annual([0.4, 40]).assign(
            Unit=["Share", "%"]
        ),
    }
    release = tmp_path / "PUBLISH-TIMES-NZ/releases/v308"
    run = tmp_path / "SOLVE-TIMES-NZ/build/solves/steady-v3.0.9-20261124T010000Z"
    for root, sid, factor in [
        (release, "steady-v308", 1),
        (run / "postprocessed", "steady-v3.0.9", 1.1),
    ]:
        files = ["raw_results.parquet"]
        for name, frame in data.items():
            relative = f"summaries/{name}.csv"
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            frame = frame.assign(Scenario=sid, Value=frame.Value * factor)
            if (
                "SectorGroup" in frame
                and name.startswith("electricity/")
                and factor != 1
            ):
                frame = frame.assign(SectorGroup="Transport")
            frame.to_csv(path, index=False)
            files.append(relative)
        pd.DataFrame({"Scenario": [sid], "PV": [1.0]}).to_parquet(
            root / "raw_results.parquet", index=False
        )
        if factor != 1:
            (run / "manifest.json").write_text(
                json.dumps(
                    {
                        "case_name": "steady",
                        "scenario_name": sid,
                        "execution": {
                            "status": "completed",
                            "completed_at": "2026-11-24T02:00:00Z",
                        },
                        "postprocessing": {"status": "completed", "files": files},
                    }
                )
            )
    extra = (
        release / "summaries/electricity/electricity_generation_by_technology_group.csv"
    )
    annual([2], "TWh", TechnologyGroup=["Wind"]).assign(Scenario="steady-v308").to_csv(
        extra, index=False
    )
    (release / "release-manifest.json").write_text(
        json.dumps(
            {
                "format_version": 1,
                "release_name": "v308",
                "source": {"type": "legacy", "legacy_source": "synthetic"},
                "created_at": "2026-11-24T00:00:00Z",
                "scenarios": [{"id": "steady-v308", "label": "Steady"}],
            }
        )
    )
    return tmp_path


def test_comparisons_preserve_unmatched_keys_nulls_zero_baselines_and_units():
    baseline = pd.DataFrame(
        {
            "Type": ["A", "B", "C", "D", "E"],
            "Period": [2030] * 5,
            "Unit": ["PJ"] * 5,
            "Value": [0.0, 0.0, 10.0, 1.0, float("nan")],
        }
    )
    candidate = baseline.assign(Value=[0, 2, 10.5, 2, 3]).loc[
        lambda df: df.Type.ne("D")
    ]
    candidate = pd.concat([candidate, annual([5], Type=["F"])], ignore_index=True)
    compared = period_comparison([baseline, candidate], "Type", 0.05).set_index("Type")
    assert compared.loc["A", "Difference"] == 0
    assert pd.isna(compared.loc["A", "PercentDifference"])
    assert not compared.loc["A", "ExceedsTolerance"]
    assert compared.loc["B", "ExceedsTolerance"]
    assert not compared.loc["C", "ExceedsTolerance"]
    assert pd.isna(compared.loc["D", "Value_candidate"])
    assert pd.isna(compared.loc["F", "Value_baseline"])
    assert compared.loc[["D", "E", "F"], "Difference"].isna().all()
    assert compared.loc[["D", "E", "F"], "ExceedsTolerance"].isna().all()
    assert len(compared) == 6
    content = comparison_accordion(
        compared.reset_index(), "Type", "PJ", ["Baseline: <old>", "Candidate"]
    )
    assert "Baseline: &lt;old&gt;" in content and "N/A" in content
    assert "Availability" not in content and "Assessment" not in content
    assert {"Availability", "Assessment", "Status"}.isdisjoint(compared.columns)
    assert content.count('class="over-tolerance"') == 1


def test_nz_timestamp_handles_summer_winter_and_missing_timezone():
    assert nz_timestamp("2026-11-17T03:51:36Z") == "17 Nov 2026, 04:51 PM NZDT"
    assert nz_timestamp("2026-06-01T23:30:00+00:00") == "02 Jun 2026, 11:30 AM NZST"
    with pytest.raises(ValueError, match="timezone"):
        nz_timestamp("2026-11-17T03:51:36")


def test_renewable_share_assessment_uses_relative_change_and_labels_percentage_points():
    baseline = annual([63, 80, 0, 0, float("nan")], "%").assign(
        Period=[2030, 2035, 2040, 2045, 2050]
    )
    candidate = baseline.assign(Value=[76, 84, 0, 1, 99])
    compared = period_comparison([baseline, candidate], None, 0.05)
    assert compared.Difference.iloc[0] == 13
    assert compared.PercentDifference.iloc[0] == pytest.approx(20.6349206349)
    assert compared.ExceedsTolerance.iloc[:4].tolist() == [True, False, False, True]
    assert compared.PercentDifference.iloc[2:4].isna().all()
    assert pd.isna(compared.ExceedsTolerance.iloc[4])
    assert compared.DifferenceUnit.eq("percentage points").all()
    content = comparison_accordion(compared, None, "%", ["Baseline", "Candidate"])
    assert "Difference (percentage points)" in content
    assert "Relative difference (%)" in content


def test_renewable_reader_selects_prepared_percent_rows_without_conversion(monkeypatch):
    frame = annual([0.63, 63]).assign(Unit=["Share", "%"])
    monkeypatch.setattr(report_inputs, "load_summary", lambda *_: frame)
    selected = read_metric(
        {}, "indicators/renewable_generation_share", None, "%", {"Unit": "%"}
    )
    assert len(selected) == 1 and selected.Value.item() == 63
    assert selected.Unit.item() == "%"


def test_panels_keep_layout_colours_and_show_negative_values():
    for count in [2, 3, 5, 6]:
        frames = [annual([1] * count, Type=[str(i) for i in range(count)])] * 2
        figure = chart_figure(frames, "Type", "PJ", 0.05)
        assert len(figure.axes) == count
        for axis in figure.axes:
            assert axis.get_subplotspec().get_gridspec().ncols == min(3, count)
            assert [line.get_color() for line in axis.lines] == ["#447474", "#C346CE"]
            assert axis.get_ylim()[0] == 0
            assert axis.get_legend() is None
    assert "data:image/svg+xml;base64," in detail_chart(frames, "Type", "PJ", 0.05)
    negative = annual([-1])
    assert (
        chart_figure([negative, negative], None, "PJ", 0.05).axes[0].get_ylim()[0] < -1
    )


def test_missing_charts_and_unmatched_years_are_not_tolerance_failures():
    empty = annual([])
    assert detail_chart([empty, empty], None, "PJ", 0.05) == "<p>no data found</p>"
    content = detail_chart([empty, annual([1])], None, "PJ", 0.05)
    assert "Baseline data unavailable" in content
    assert "data:image/svg+xml;base64," in content
    baseline = {2025: 100, 2030: 100, 2035: 100, 2040: 0, 2045: 0, 2050: 10}
    candidate = {2025: 104, 2030: 105, 2035: 106, 2040: 0, 2045: 1}
    assert list(different_period_spans(baseline, candidate, 0.05)) == [
        (2032.5, 2037.5),
        (2042.5, 2047.5),
    ]


@pytest.mark.parametrize(
    "frame,group,annual_flag",
    [
        (pd.DataFrame({"Value": [1]}), None, True),
        (annual([1], "GWh"), None, True),
        (annual([1, 2]), None, True),
        (annual([1], SectorGroup=[""]), "SectorGroup", True),
        (annual([1]).assign(Period="2030.5"), None, True),
        (pd.DataFrame({"Unit": ["NZDb", "NZDb"], "Value": [1, 2]}), None, False),
        (pd.DataFrame({"Unit": ["NZDb"], "Value": [float("nan")]}), None, False),
    ],
)
def test_metric_reader_rejects_malformed_supplied_data(
    monkeypatch, frame, group, annual_flag
):
    monkeypatch.setattr(report_inputs, "load_summary", lambda *_: frame)
    with pytest.raises(ValueError):
        read_metric(
            {}, "fake", group, "PJ" if annual_flag else "NZDb", {}, annual=annual_flag
        )


def test_metric_reader_preserves_supplied_years_and_null_values(monkeypatch):
    frame = annual([float("nan")]).assign(Period="2030")
    monkeypatch.setattr(report_inputs, "load_summary", lambda *_: frame)
    result = read_metric({}, "fake", None, "PJ", {})
    assert len(result) == 1 and result.Period.item() == 2030
    assert result.Period.dtype == "int64" and result.Value.isna().all()


def test_cli_generates_offline_html_and_exact_prepared_comparisons(
    repository, monkeypatch, capsys
):
    monkeypatch.setattr("sys.argv", ["qa-times-nz", "generate_qa"])
    cli.main()
    output = repository / "QA-TIMES-NZ/build"
    content = (output / REPORT_NAME).read_text()
    assert "Report:" in capsys.readouterr().out
    assert "data:image/svg+xml;base64," in content
    assert "<script src=" not in content and "<link " not in content
    assert "Published &lt;old&gt;" in content and "Published <old>" not in content
    for title in [
        "Summary",
        "Electricity",
        "Oil and gas",
        "Renewables",
        "Emissions",
        "Selected inputs",
    ]:
        assert title in content
    assert "Candidate data unavailable" in content and "no data found" in content
    for column in ["Result root", "Manifest", "Run timestamp (UTC)", "Model version"]:
        assert f">{column}</th>" not in content
    assert "source manifest</summary>" not in content
    compared = pd.read_csv(output / COMPARISONS_NAME)
    totals = compared.loc[compared.Metric.eq("electricity-demand-total")]
    assert totals.Value_baseline.item() == 10
    assert totals.Value_candidate.item() == 11
    assert totals.Difference.item() == 1
    sectors = compared.loc[compared.Metric.eq("electricity-demand-sector")]
    assert len(sectors) == 2
    assert sectors.Difference.isna().all() and sectors.ExceedsTolerance.isna().all()
    objective = compared.loc[compared.Metric.eq("objective_function")]
    assert objective.Period.isna().all() and objective.ExceedsTolerance.isna().all()
    assert {"Availability", "Assessment", "Status"}.isdisjoint(compared.columns)
    assert objective.Difference.item() == 1
    renewable = compared.loc[compared.Metric.eq("renewable-generation-share")]
    assert renewable.Value_baseline.item() == 63
    assert renewable.Value_candidate.item() == pytest.approx(69.3)
    assert renewable.PercentDifference.item() == pytest.approx(10)
    assert renewable.DifferenceUnit.item() == "percentage points"
    assert renewable.ExceedsTolerance.item()
    assert set(compared.BaselineScenario) == {"steady-v308"}
    assert set(compared.CandidateScenario) == {"steady-v3.0.9"}
    assert not compared.Metric.eq("gas-supply-total").any()


def test_dev_config_generation_is_exclusive_and_dev_report_reuses_output_paths(
    repository, monkeypatch
):
    qa = repository / "QA-TIMES-NZ"
    main = (qa / "report_config.toml").read_bytes()
    with pytest.raises(FileNotFoundError, match="init-dev-config"):
        build_report(dev=True)
    monkeypatch.setattr("sys.argv", ["qa-times-nz", "init-dev-config"])
    cli.main()
    dev_path = qa / "report_config_dev.toml"
    assert dev_path.read_bytes() == main
    dev_path.write_text(dev_path.read_text().replace("0.05", "0.2"))
    dev_before = dev_path.read_bytes()
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 2 and dev_path.read_bytes() == dev_before
    output = qa / "build"
    output.mkdir()
    (output / REPORT_NAME).write_text("Previous main report")
    (output / COMPARISONS_NAME).write_text("Previous main comparisons")
    monkeypatch.setattr("sys.argv", ["qa-times-nz", "generate_qa", "--dev"])
    cli.main()
    assert "Previous main report" not in (output / REPORT_NAME).read_text()
    assert not (output / "reports").exists()
    assert (qa / "report_config.toml").read_bytes() == main
    compared = pd.read_csv(output / COMPARISONS_NAME)
    assert not compared.loc[
        compared.Metric.eq("electricity-demand-total"), "ExceedsTolerance"
    ].item()


def test_packaging_the_same_candidate_changes_only_provenance(repository):
    path = build_report()
    original = (comparisons_path(path)).read_bytes()
    run = repository / "SOLVE-TIMES-NZ/build/solves/steady-v3.0.9-20261124T010000Z"
    build_release(
        "candidate", [run / "postprocessed"], repository / "PUBLISH-TIMES-NZ/releases"
    )
    config = repository / "QA-TIMES-NZ/report_config.toml"
    text = config.read_text().replace(
        'source = "SOLVE"\nscenario = "steady"',
        'source = "RELEASE"\nrelease = "candidate"\nscenario = "steady-v3.0.9"',
    )
    config.write_text(text)
    path = build_report()
    assert original == (comparisons_path(path)).read_bytes()
    assert "<td>candidate</td>" in path.read_text()


def test_invalid_input_fails_before_report_outputs_are_written(repository, monkeypatch):
    path = (
        repository
        / "SOLVE-TIMES-NZ/build/solves/steady-v3.0.9-20261124T010000Z/postprocessed/summaries/electricity/electricity_demand.csv"
    )
    frame = pd.read_csv(path).assign(Unit="GWh")
    frame.to_csv(path, index=False)
    monkeypatch.setattr("sys.argv", ["qa-times-nz", "generate_qa"])
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 2
    assert not (repository / "QA-TIMES-NZ/build").exists()
