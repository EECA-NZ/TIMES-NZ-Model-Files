"""Command-line interface for resolving and building DD cases."""

from __future__ import annotations

import argparse
from pathlib import Path

from solve_times_nz.case import (
    DEFAULT_INPUT_ROOT,
    REPOSITORY_ROOT,
    CaseConfigurationError,
    build_case,
    resolve_case,
)
from solve_times_nz.execution import stage_case

DEFAULT_LOCAL_CONFIG = (
    REPOSITORY_ROOT / "SOLVE-TIMES-NZ" / "config" / "solve.local.toml"
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="solve-times-nz")
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("resolve", "build"):
        subparser = commands.add_parser(command)
        subparser.add_argument("case", type=Path, help="Path to the case TOML manifest")
        subparser.add_argument("--input-root", type=Path, default=DEFAULT_INPUT_ROOT)
        subparser.add_argument(
            "--groups", type=Path, help="Override config/input-groups.toml"
        )
        if command == "build":
            subparser.add_argument(
                "--output", type=Path, required=True, help="New case directory"
            )
    stage = commands.add_parser(
        "stage", help="Copy a generated case to an executor staging root"
    )
    stage.add_argument("case_dir", type=Path, help="Generated case directory")
    stage.add_argument("--local-config", type=Path, default=DEFAULT_LOCAL_CONFIG)
    stage.add_argument("--run-id", help="Unique suffix for the staged run directory")
    return parser


def main() -> None:
    """Resolve a case, optionally exporting its DD inputs."""
    arguments = _parser().parse_args()
    try:
        if arguments.command == "stage":
            print(
                stage_case(arguments.case_dir, arguments.local_config, arguments.run_id)
            )
            return
        case = resolve_case(arguments.case, arguments.input_root, arguments.groups)
        if arguments.command == "resolve":
            for path in case.files:
                print(path.relative_to(case.input_root).as_posix())
            return
        build_case(case, arguments.output)
    except CaseConfigurationError as error:
        raise SystemExit(f"error: {error}") from error


if __name__ == "__main__":
    main()
