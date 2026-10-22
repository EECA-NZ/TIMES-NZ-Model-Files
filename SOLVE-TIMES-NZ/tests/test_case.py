"""Tests for declarative workbook selection and DD export orchestration."""

import json
import subprocess
from pathlib import Path

import pytest
from solve_times_nz.case import CaseConfigurationError, build_case, resolve_case


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
    manifest = tmp_path / "cases" / "steady.toml"
    _write(manifest, 'name = "steady"\ngroups = ["steady"]\n')
    return input_root, groups, manifest


def test_resolve_expands_composite_groups_in_order(tmp_path: Path) -> None:
    input_root, groups, manifest = _configuration(tmp_path)

    case = resolve_case(manifest, input_root, groups)

    assert case.name == "steady"
    assert [path.name for path in case.files] == ["Base.xlsx", "Steady.xlsx"]


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

    def fake_runner(command, **_kwargs):
        commands.append(command)
        for name in ("ts.dd", "milestonyr.dd", "output.dd"):
            (output / name).write_text(name, encoding="utf-8")
        return subprocess.CompletedProcess(command, 0)

    build_case(case, output, runner=fake_runner)

    assert commands[0][1:3] == ["-m", "solve_times_nz.xl2times_compat"]
    written = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert [item["path"] for item in written["inputs"]] == ["Base.xlsx", "Steady.xlsx"]


def test_build_does_not_overwrite_case(tmp_path: Path) -> None:
    input_root, groups, manifest = _configuration(tmp_path)
    case = resolve_case(manifest, input_root, groups)
    output = tmp_path / "build" / "steady"
    output.mkdir(parents=True)

    with pytest.raises(CaseConfigurationError, match="Refusing to overwrite"):
        build_case(case, output)
