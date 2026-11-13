"""Command-line entry points for PUBLISH-TIMES-NZ."""

from __future__ import annotations

import argparse
from pathlib import Path

from publish_times_nz.release_builder import build_release, import_legacy_release


DEFAULT_RELEASES_ROOT = Path(__file__).parents[2] / "releases"


def main() -> None:
    """Build or import a named local release."""
    parser = argparse.ArgumentParser(prog="publish-times-nz")
    commands = parser.add_subparsers(dest="command", required=True)

    build = commands.add_parser("build", help="Build a release from solver outputs")
    build.add_argument("release_name")
    build.add_argument("source_directory", nargs="+", type=Path)
    build.add_argument("--releases-root", default=DEFAULT_RELEASES_ROOT, type=Path)

    legacy = commands.add_parser("import-legacy", help="Import legacy result Parquets")
    legacy.add_argument("release_name")
    legacy.add_argument("source_directory", type=Path)
    legacy.add_argument("--legacy-source")
    legacy.add_argument("--releases-root", default=DEFAULT_RELEASES_ROOT, type=Path)

    arguments = parser.parse_args()
    if arguments.command == "build":
        bundle = build_release(
            arguments.release_name,
            arguments.source_directory,
            arguments.releases_root,
        )
    else:
        bundle = import_legacy_release(
            arguments.release_name,
            arguments.source_directory,
            arguments.releases_root,
            arguments.legacy_source,
        )
    print(bundle.path)
