"""Tests for declarative workbook selection and DD export orchestration."""

import json
import subprocess
from pathlib import Path

import pytest
import solve_times_nz.execution as execution
from solve_times_nz.case import (
    CaseConfigurationError,
    build_case,
    resolve_case,
    versioned_case_name,
)
from solve_times_nz.execution import load_executor, solve_case


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _configuration(tmp_path: Path) -> tuple[Path, Path, Path]:
    input_root = tmp_path / "inputs"
    for name in ("Base.xlsx", "Steady.xlsx", "Shift.xlsx"):
        _write(input_root / name, "workbook")
    groups = tmp_path / "config" / "input-groups.toml"
    _write(
        groups,
        """[groups.base]\nfiles = [\"Base.xlsx\"]\n\n[groups.steady]\nincludes = [\"base\"]\nfiles = [\"Steady.xlsx\"]\n\n[groups.shift]\nincludes = [\"base\"]\nfiles = [\"Shift.xlsx\"]\n""",
    )
    _write(
        groups.with_name("input-order.toml"),
        'files = ["Base.xlsx", "Steady.xlsx", "Shift.xlsx"]\n',
    )
    manifest = tmp_path / "cases" / "steady.toml"
    _write(
        manifest,
        'name = "steady"\ngroups = ["steady"]\n\n[solve]\nexecutor = "test"\n',
    )
    return input_root, groups, manifest


def test_resolve_expands_composite_groups_in_order(tmp_path: Path) -> None:
    input_root, groups, manifest = _configuration(tmp_path)

    case = resolve_case(manifest, input_root, groups)

    assert case.name == "steady"
    assert [path.name for path in case.files] == ["Base.xlsx", "Steady.xlsx"]


def test_resolve_uses_file_order_not_group_order(tmp_path: Path) -> None:
    input_root, groups, manifest = _configuration(tmp_path)
    manifest.write_text(
        'name = "test"\ngroups = ["shift", "base"]\n\n[solve]\nexecutor = "test"\n',
        encoding="utf-8",
    )

    case = resolve_case(manifest, input_root, groups)

    assert [path.name for path in case.files] == ["Base.xlsx", "Shift.xlsx"]


def test_resolve_rejects_selected_file_without_order_entry(tmp_path: Path) -> None:
    input_root, groups, manifest = _configuration(tmp_path)
    _write(groups.with_name("input-order.toml"), 'files = ["Base.xlsx"]\n')

    with pytest.raises(CaseConfigurationError, match="no file-order entry"):
        resolve_case(manifest, input_root, groups)


def test_resolve_rejects_empty_pattern(tmp_path: Path) -> None:
    input_root, groups, manifest = _configuration(tmp_path)
    groups.write_text('[groups.steady]\nfiles = ["absent.xlsx"]\n', encoding="utf-8")

    with pytest.raises(CaseConfigurationError, match="matched no files"):
        resolve_case(manifest, input_root, groups)


def test_resolve_rejects_group_cycle(tmp_path: Path) -> None:
    input_root, groups, manifest = _configuration(tmp_path)
    groups.write_text(
        '[groups.steady]\nincludes = ["other"]\n\n[groups.other]\nincludes = ["steady"]\n',
        encoding="utf-8",
    )

    with pytest.raises(CaseConfigurationError, match="inclusion cycle"):
        resolve_case(manifest, input_root, groups)


def test_build_runs_wrapper_and_writes_manifest(tmp_path: Path) -> None:
    input_root, groups, manifest = _configuration(tmp_path)
    case = resolve_case(manifest, input_root, groups)
    output = tmp_path / "build" / "steady"
    commands: list[list[str]] = []
    working_directories: list[Path] = []

    def fake_runner(command, **kwargs):
        commands.append(command)
        working_directories.append(kwargs["cwd"])
        for name in ("ts.dd", "milestonyr.dd", "output.dd"):
            (output / name).write_text(name, encoding="utf-8")
        return subprocess.CompletedProcess(command, 0)

    build_case(case, output, runner=fake_runner)

    assert commands[0][1:3] == ["-m", "solve_times_nz.xl2times_compat"]
    assert working_directories == [output.resolve()]
    written = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert [item["path"] for item in written["inputs"]] == ["Base.xlsx", "Steady.xlsx"]
    assert written["executor"] == "test"
    assert (output / "steady.run").is_file()
    assert "OPTION OPTFILE=1;" not in (output / "steady.run").read_text(
        encoding="utf-8"
    )
    assert (output / "cplex.opt").read_text(encoding="utf-8") == (
        "scaind 1\n"
        "rerun yes\n"
        "iis 1\n"
        "lpmethod 4\n"
        "baralg 1\n"
        "barcrossalg 0\n"
        "barorder 0\n"
        "THREADS=7\n"
        "aggind 3\n"
        "Names no\n"
        "advind=0\n"
    )


def test_build_replaces_previous_generated_case(tmp_path: Path) -> None:
    input_root, groups, manifest = _configuration(tmp_path)
    case = resolve_case(manifest, input_root, groups)
    output = tmp_path / "build" / "steady"

    def fake_runner(_command, **_kwargs):
        for name in ("ts.dd", "milestonyr.dd", "output.dd"):
            (output / name).write_text(name, encoding="utf-8")
        return subprocess.CompletedProcess([], 0)

    build_case(case, output, runner=fake_runner)
    (output / "stale.txt").write_text("old", encoding="utf-8")

    build_case(case, output, runner=fake_runner)

    assert not (output / "stale.txt").exists()
    assert (output / "manifest.json").is_file()


def test_solve_stages_case_and_invokes_windows_gams(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    input_root, groups, manifest = _configuration(tmp_path)
    case = resolve_case(manifest, input_root, groups)
    output = tmp_path / "build" / "steady"

    def fake_export(_command, **_kwargs):
        for name in ("ts.dd", "milestonyr.dd", "output.dd"):
            (output / name).write_text(name, encoding="utf-8")
        return subprocess.CompletedProcess([], 0)

    build_case(case, output, runner=fake_export)
    staging_root = tmp_path / "staging"
    staging_root.mkdir()
    results_root = tmp_path / "results"
    monkeypatch.setattr(execution, "RESULTS_ROOT", results_root)
    gams_root = tmp_path / "gams"
    gams_root.mkdir()
    (gams_root / "gams.exe").write_text("", encoding="utf-8")
    (gams_root / "gdx2veda.exe").write_text("", encoding="utf-8")
    times_root = tmp_path / "times"
    times_root.mkdir()
    (times_root / "_times.g00").write_text("", encoding="utf-8")
    (times_root / "times2veda.vdd").write_text("", encoding="utf-8")
    local_config = tmp_path / "solve.local.toml"
    _write(
        local_config,
        "[executors.test]\n"
        f'staging_root = "{staging_root}"\n'
        f'gams_system_dir = "{gams_root}"\n'
        f'times_source_dir = "{times_root}"\n',
    )
    commands: list[list[str]] = []
    working_directories: list[Path] = []

    def fake_gams(command, **kwargs):
        commands.append(command)
        working_directories.append(kwargs["cwd"])
        staged_dir = staging_root / f"{versioned_case_name('steady')}-trial"
        (staged_dir / "steady.vd").write_text("results", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0)

    destination = solve_case(
        output,
        local_config,
        "trial",
        runner=fake_gams,
        windows_path=lambda path: f"C:\\Program Files\\{path.name}",
    )

    assert destination == results_root / f"{versioned_case_name('steady')}-trial"
    assert commands[0] == [
        str(gams_root / "gams.exe"),
        "steady.run",
        "IDIR=C:\\Program Files\\times",
        "GDX=GAMSSAVE\\steady",
        "PS=99999",
        "R=C:\\Program Files\\times\\_times",
        "LO=1",
        "OPTFILE=1",
    ]
    assert commands[1] == [
        str(gams_root / "gdx2veda.exe"),
        "GAMSSAVE\\steady",
        "C:\\Program Files\\times\\times2veda.vdd",
        "steady",
    ]
    assert working_directories == [
        staging_root / f"{versioned_case_name('steady')}-trial"
    ] * 2
    assert (destination / "steady.vd").is_file()
    solved_manifest = json.loads((destination / "manifest.json").read_text())
    assert solved_manifest["execution"]["status"] == "completed"
    assert solved_manifest["execution"]["gdx2veda_command"] == commands[1]


def test_windows_path_rejects_unc_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fake_run(*_args, **_kwargs):
        return subprocess.CompletedProcess(
            [], 0, stdout="\\\\wsl.localhost\\Ubuntu\\home\\developer\\runs\n"
        )

    monkeypatch.setattr(execution.subprocess, "run", fake_run)

    with pytest.raises(CaseConfigurationError, match="drive-backed executor paths"):
        execution._windows_path(tmp_path / "runs")


def test_solve_reports_gdx2veda_failures_separately(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    input_root, groups, manifest = _configuration(tmp_path)
    case = resolve_case(manifest, input_root, groups)
    output = tmp_path / "build" / "steady"

    def fake_export(_command, **_kwargs):
        for name in ("ts.dd", "milestonyr.dd", "output.dd"):
            (output / name).write_text(name, encoding="utf-8")
        return subprocess.CompletedProcess([], 0)

    build_case(case, output, runner=fake_export)
    staging_root = tmp_path / "staging"
    staging_root.mkdir()
    gams_root = tmp_path / "gams"
    gams_root.mkdir()
    (gams_root / "gams.exe").write_text("", encoding="utf-8")
    (gams_root / "gdx2veda.exe").write_text("", encoding="utf-8")
    times_root = tmp_path / "times"
    times_root.mkdir()
    (times_root / "_times.g00").write_text("", encoding="utf-8")
    (times_root / "times2veda.vdd").write_text("", encoding="utf-8")
    local_config = tmp_path / "solve.local.toml"
    _write(
        local_config,
        "[executors.test]\n"
        f'staging_root = "{staging_root}"\n'
        f'gams_system_dir = "{gams_root}"\n'
        f'times_source_dir = "{times_root}"\n',
    )

    def gdx2veda_fails(command, **_kwargs):
        if command[0] == str(gams_root / "gdx2veda.exe"):
            raise subprocess.CalledProcessError(7, command)
        return subprocess.CompletedProcess(command, 0)

    with pytest.raises(RuntimeError, match="GDX2VEDA failed with exit code 7"):
        solve_case(
            output,
            local_config,
            "gdx2veda-failure",
            runner=gdx2veda_fails,
            windows_path=lambda path: f"WIN:{path.name}",
        )

    staged_manifest = json.loads(
        (
            staging_root
            / f"{versioned_case_name('steady')}-gdx2veda-failure"
            / "manifest.json"
        ).read_text()
    )
    assert staged_manifest["execution"]["status"] == "gdx2veda_failed"


def test_solve_diagnostic_exports_and_collects_matrix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    input_root, groups, manifest = _configuration(tmp_path)
    case = resolve_case(manifest, input_root, groups)
    output = tmp_path / "build" / "steady"

    def fake_export(_command, **_kwargs):
        for name in ("ts.dd", "milestonyr.dd", "output.dd"):
            (output / name).write_text(name, encoding="utf-8")
        return subprocess.CompletedProcess([], 0)

    build_case(case, output, runner=fake_export)
    staging_root = tmp_path / "staging"
    staging_root.mkdir()
    results_root = tmp_path / "results"
    monkeypatch.setattr(execution, "RESULTS_ROOT", results_root)
    gams_root = tmp_path / "gams"
    gams_root.mkdir()
    (gams_root / "gams.exe").write_text("", encoding="utf-8")
    (gams_root / "gdx2veda.exe").write_text("", encoding="utf-8")
    times_root = tmp_path / "times"
    times_root.mkdir()
    (times_root / "_times.g00").write_text("", encoding="utf-8")
    (times_root / "times2veda.vdd").write_text("", encoding="utf-8")
    local_config = tmp_path / "solve.local.toml"
    _write(
        local_config,
        "[executors.test]\n"
        f'staging_root = "{staging_root}"\n'
        f'gams_system_dir = "{gams_root}"\n'
        f'times_source_dir = "{times_root}"\n',
    )
    commands: list[list[str]] = []
    working_directories: list[Path] = []

    def fake_gams(command, **kwargs):
        commands.append(command)
        working_directories.append(kwargs["cwd"])
        staged_dir = staging_root / f"{versioned_case_name('steady')}-diagnostic"
        (staged_dir / "steady.vd").write_text("results", encoding="utf-8")
        if command[1] == "diagnostic-steady.run":
            (staged_dir / execution.DIAGNOSTIC_MATRIX_FILE).write_text(
                "matrix", encoding="utf-8"
            )
            (staged_dir / execution.DIAGNOSTIC_DICTIONARY_FILE).write_text(
                "dictionary", encoding="utf-8"
            )
            (staged_dir / execution.DIAGNOSTIC_LP_FILE).write_text(
                "lp", encoding="utf-8"
            )
            raise subprocess.CalledProcessError(3, command)
        return subprocess.CompletedProcess(command, 0)

    destination = solve_case(
        output,
        local_config,
        "diagnostic",
        diagnostic=True,
        runner=fake_gams,
        windows_path=lambda path: f"WIN:{path.name}",
    )

    assert len(commands) == 3
    assert (
        working_directories
        == [staging_root / f"{versioned_case_name('steady')}-diagnostic"] * 3
    )
    assert "OPTFILE=1" in commands[0]
    assert commands[1][0] == str(gams_root / "gdx2veda.exe")
    assert commands[2][1] == "diagnostic-steady.run"
    assert "OPTFILE=1" in commands[2]
    diagnostic_run = (
        staging_root
        / f"{versioned_case_name('steady')}-diagnostic"
        / "diagnostic-steady.run"
    ).read_text()
    assert "OPTION LP=convert;" in diagnostic_run
    assert (destination / "diagnostics" / execution.DIAGNOSTIC_MATRIX_FILE).is_file()
    assert (
        destination / "diagnostics" / execution.DIAGNOSTIC_DICTIONARY_FILE
    ).is_file()
    assert (destination / "diagnostics" / execution.DIAGNOSTIC_LP_FILE).is_file()
    solved_manifest = json.loads((destination / "manifest.json").read_text())
    assert solved_manifest["diagnostics"]["type"] == "gams-convert-lp"
    assert solved_manifest["execution"]["diagnostic_exit_code"] == 3
