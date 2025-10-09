#!/usr/bin/env python3
"""
pylint_precommit.py

Why this exists
---------------
We have a repo with multiple projects. pre-commit runs from the *repo root*
and passes file paths like "PREPARE-TIMES-NZ/src/.../file.py".

This hook runs pylint via:
    poetry --directory PREPARE-TIMES-NZ run ...

...which sets cwd to the *package root*:
    cwd == ".../TIMES-NZ-Model-Files/PREPARE-TIMES-NZ"

So pylint should receive paths relative to the package root, e.g. "src/.../file.py".
This wrapper normalizes the incoming paths and forwards them to pylint.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# We expect to be executed with cwd == package root because of the Poetry command.
PACKAGE_ROOT = Path.cwd()
PACKAGE_NAME = PACKAGE_ROOT.name  # e.g. "PREPARE-TIMES-NZ"
RCFILE = PACKAGE_ROOT / "pyproject.toml"

# Ensure we're in the package root (script lives in repo_root/tools/)
try:
    assert Path(__file__).resolve().parent.parent == PACKAGE_ROOT
except AssertionError:
    print(
        "Warning: running outside package root; " \
        "path rewriting may be wrong.",
        file=sys.stderr,
    )
    print(f"Package Root: {PACKAGE_ROOT}")
    print(f"Running in: {Path(__file__).resolve().parent.parent}")

# Strip a leading "PREPARE-TIMES-NZ/" or "PREPARE-TIMES-NZ\"
_LEADING_PACKAGE_PREFIX = re.compile(
    rf"^(?:{re.escape(PACKAGE_NAME)})[\\/]", re.IGNORECASE
)


def _to_package_relative(arg: str) -> str:
    """
    Convert a repo-root path to a package-root path.

    Examples (cwd == PREPARE-TIMES-NZ):
      "PREPARE-TIMES-NZ/src/x.py" -> "src/x.py"
      "src/x.py"                  -> "src/x.py"
      "PREPARE-TIMES-NZ\\dodo.py" -> "dodo.py"
    """
    return _LEADING_PACKAGE_PREFIX.sub("", arg)


def main(argv: list[str]) -> int:
    """
    Main entry point for the script.
    """
    files = [_to_package_relative(a) for a in argv]
    if not files:
        print("No files to lint: exiting.")
        return 0

    cmd = [
        sys.executable,
        "-m",
        "pylint",
        f"--rcfile={RCFILE}",
        "--fail-under=10.0",
        *files,
    ]
    result = subprocess.run(cmd, check=False)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
