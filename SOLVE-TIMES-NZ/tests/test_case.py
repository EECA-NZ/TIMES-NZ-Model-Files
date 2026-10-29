"""Tests for declarative workbook selection and DD export orchestration."""

import json
import subprocess
from pathlib import Path

import pytest
import solve_times_nz.execution as execution
from solve_times_nz.case import CaseConfigurationError, build_case, resolve_case
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

    def fake_gams(command, **_kwargs):
        commands.append(command)
        staged_dir = staging_root / "steady-trial"
        (staged_dir / "steady.vd").write_text("results", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0)

    destination = solve_case(
        output,
        local_config,
        "trial",
        runner=fake_gams,
        windows_path=lambda path: f"WIN:{path.name}",
    )

    assert destination == results_root / "steady-trial"
    assert commands[0][:3] == ["cmd.exe", "/d", "/c"]
    assert "GAMS steady.run IDIR=WIN:times" in commands[0][3]
    assert "OPTFILE=1" in commands[0][3]
    assert "GDX2VEDA GAMSSAVE\\steady" in commands[0][3]
    assert (destination / "steady.vd").is_file()
    solved_manifest = json.loads((destination / "manifest.json").read_text())
    assert solved_manifest["execution"]["status"] == "completed"


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

    def fake_gams(command, **_kwargs):
        commands.append(command)
        staged_dir = staging_root / "steady-diagnostic"
        (staged_dir / "steady.vd").write_text("results", encoding="utf-8")
        if "GAMS diagnostic-steady.run" in command[3]:
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

    assert len(commands) == 2
    assert "OPTFILE=1" in commands[0][3]
    assert "GAMS diagnostic-steady.run" in commands[1][3]
    assert "OPTFILE=1" in commands[1][3]
    diagnostic_run = (
        staging_root / "steady-diagnostic" / "diagnostic-steady.run"
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
