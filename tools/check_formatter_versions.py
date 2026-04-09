#!/usr/bin/env python3
"""
Ensure formatter versions are aligned between Poetry and pre-commit.
"""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POETRY_LOCK = ROOT / "PREPARE-TIMES-NZ/poetry.lock"
PRE_COMMIT_CONFIG = ROOT / ".pre-commit-config.yaml"

PRE_COMMIT_REPOS = {
    "black": "https://github.com/psf/black",
    "isort": "https://github.com/pycqa/isort",
}


def poetry_lock_version(package_name: str) -> str:
    """
    Read the locked version for a named package from Poetry's lockfile.
    """
    lock_data = tomllib.loads(POETRY_LOCK.read_text(encoding="utf-8"))
    for package in lock_data["package"]:
        if package["name"] == package_name:
            return package["version"]

    raise ValueError(f"Package {package_name!r} not found in {POETRY_LOCK}")


def pre_commit_rev(repo_url: str) -> str:
    """
    Read the pinned revision for a pre-commit repo from the YAML config.
    """
    text = PRE_COMMIT_CONFIG.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"repo:\s*{re.escape(repo_url)}(?:\n[ \t#].*)*\n[ \t]*rev:\s*([^\s]+)",
        re.MULTILINE,
    )
    match = pattern.search(text)
    if match:
        return match.group(1)

    raise ValueError(f"Repo {repo_url!r} not found in {PRE_COMMIT_CONFIG}")


def main() -> int:
    """
    Validate that pre-commit formatter pins match Poetry's locked versions.
    """
    mismatches: list[str] = []
    for package_name, repo_url in PRE_COMMIT_REPOS.items():
        poetry_version = poetry_lock_version(package_name)
        hook_version = pre_commit_rev(repo_url)
        if poetry_version != hook_version:
            mismatches.append(
                f"{package_name}: Poetry lock has {poetry_version}, "
                f"pre-commit pins {hook_version}"
            )

    if mismatches:
        print("Formatter version mismatch detected:", file=sys.stderr)
        for mismatch in mismatches:
            print(f"- {mismatch}", file=sys.stderr)
        return 1

    print("Formatter versions are aligned between Poetry and pre-commit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
