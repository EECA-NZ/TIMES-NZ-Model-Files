"""Tests for default CLI locations and overrides."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import solve_times_nz.cli as cli


def test_build_defaults_to_case_name_under_build_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Build output follows the case manifest name, not its filename."""
    built: list[Path] = []
    case = SimpleNamespace(name="steady")
    monkeypatch.setattr(cli, "resolve_case", lambda *_args: case)
    monkeypatch.setattr(cli, "build_case", lambda _case, output: built.append(output))
    monkeypatch.setattr(sys, "argv", ["solve-times-nz", "build", "cases/steady.toml"])

    cli.main()

    assert built == [cli.DEFAULT_CASE_BUILD_ROOT / cli.versioned_case_name("steady")]


def test_build_accepts_an_explicit_output_override(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """An explicit output directory remains available for smoke-test cases."""
    built: list[Path] = []
    output = tmp_path / "custom-case"
    case = SimpleNamespace(name="steady")
    monkeypatch.setattr(cli, "resolve_case", lambda *_args: case)
    monkeypatch.setattr(cli, "build_case", lambda _case, path: built.append(path))
    monkeypatch.setattr(
        sys,
        "argv",
        ["solve-times-nz", "build", "cases/steady.toml", "--output", str(output)],
    )

    cli.main()

    assert built == [output]


def test_solve_postprocesses_the_completed_run(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    run_dir = tmp_path / "solve"
    postprocessed: list[tuple[Path, Path]] = []
    monkeypatch.setattr(cli, "solve_case", lambda *_args, **_kwargs: run_dir)
    monkeypatch.setattr(
        cli,
        "snapshot_metadata",
        lambda _metadata, _run: run_dir / "postprocessed/metadata",
    )
    monkeypatch.setattr(
        cli,
        "postprocess_run",
        lambda run, metadata: postprocessed.append((run, metadata))
        or run / "postprocessed",
    )
    monkeypatch.setattr(sys, "argv", ["solve-times-nz", "solve", "steady"])

    cli.main()

    assert postprocessed == [(run_dir, run_dir / "postprocessed/metadata")]
