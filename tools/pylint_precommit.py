#!/usr/bin/env python3
"""
pylint_precommit.py

Why this exists
---------------
We have a repo with multiple projects. pre-commit runs from the *repo root*
and passes file paths like "PREPARE-TIMES-NZ/src/.../file.py".

This hook runs pylint via:
    poetry --directory PREPARE-TIMES-NZ run ...

Poetry selects that project environment, but it does not change cwd for the
command. This wrapper infers the package root from the incoming paths, points
pylint at that package's pyproject.toml, and forwards package-relative paths.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _package_root_from_args(args: list[str]) -> Path:
    """Return the subproject root implied by pre-commit file paths."""
    for arg in args:
        path = Path(arg)
        if path.is_absolute():
            try:
                path = path.relative_to(REPO_ROOT)
            except ValueError:
                continue

        if not path.parts:
            continue

        candidate = REPO_ROOT / path.parts[0]
        if (candidate / "pyproject.toml").is_file():
            return candidate

    if (Path.cwd() / "pyproject.toml").is_file():
        return Path.cwd()

    raise SystemExit(
        "Could not infer subproject for pylint; expected files under a "
        "directory containing pyproject.toml."
    )


def _to_package_relative(arg: str, package_root: Path) -> str:
    """Convert a repo-root path to a package-root path."""
    path = Path(arg)
    if path.is_absolute():
        try:
            return str(path.relative_to(package_root))
        except ValueError:
            return arg

    leading_package_prefix = re.compile(
        rf"^(?:{re.escape(package_root.name)})[\\/]", re.IGNORECASE
    )
    return leading_package_prefix.sub("", arg)


def main(argv: list[str]) -> int:
    """
    Main entry point for the script.
    """
    if not argv:
        print("No files to lint: exiting.")
        return 0

    package_root = _package_root_from_args(argv)
    rcfile = package_root / "pyproject.toml"
    files = [_to_package_relative(a, package_root) for a in argv]

    cmd = [
        sys.executable,
        "-m",
        "pylint",
        f"--rcfile={rcfile}",
        "--persistent=n",
        "--fail-under=10.0",
        *files,
    ]
    result = subprocess.run(cmd, check=False, cwd=package_root)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
