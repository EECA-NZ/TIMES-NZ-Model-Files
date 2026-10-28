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
from solve_times_nz.execution import solve_case

DEFAULT_LOCAL_CONFIG = (
    REPOSITORY_ROOT / "SOLVE-TIMES-NZ" / "config" / "solve.local.toml"
)
DEFAULT_CASE_BUILD_ROOT = REPOSITORY_ROOT / "SOLVE-TIMES-NZ" / "build" / "cases"


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
        subparser.add_argument(
            "--file-order", type=Path, help="Override config/input-order.toml"
        )
        if command == "build":
            subparser.add_argument(
                "--output", type=Path, required=True, help="New case directory"
            )
    solve = commands.add_parser(
        "solve", help="Run native Windows GAMS and collect VEDA result files"
    )
    solve.add_argument("case", help="Generated case name under build/cases")
    solve.add_argument("--local-config", type=Path, default=DEFAULT_LOCAL_CONFIG)
    solve.add_argument("--run-id", help="Unique suffix for the staged run directory")
    solve.add_argument(
        "--diagnostic",
        action="store_true",
        help="Export the full named GAMS matrix and dictionary after solving",
    )
    return parser


def main() -> None:
    """Resolve a case, optionally exporting its DD inputs."""
    arguments = _parser().parse_args()
    try:
        if arguments.command == "solve":
            print(
                solve_case(
                    DEFAULT_CASE_BUILD_ROOT / arguments.case,
                    arguments.local_config,
                    arguments.run_id,
                    diagnostic=arguments.diagnostic,
                )
            )
            return
        case = resolve_case(
            arguments.case,
            arguments.input_root,
            arguments.groups,
            arguments.file_order,
        )
        if arguments.command == "resolve":
            for path in case.files:
                print(path.relative_to(case.input_root).as_posix())
            return
        build_case(case, arguments.output)
    except (CaseConfigurationError, RuntimeError) as error:
        raise SystemExit(f"error: {error}") from error


if __name__ == "__main__":
    main()
