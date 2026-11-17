"""Command-line entry points for PUBLISH-TIMES-NZ."""

from __future__ import annotations

import argparse
from pathlib import Path

from publish_times_nz.bundle_definition import build_bundle
from publish_times_nz.deployment_payload import prepare_deployment_payload
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

    bundle = commands.add_parser(
        "build-bundle", help="Build a tracked bundle for the workspace version"
    )
    bundle.add_argument("definition", type=Path)
    bundle.add_argument("--releases-root", default=DEFAULT_RELEASES_ROOT, type=Path)

    legacy = commands.add_parser("import-legacy", help="Import legacy result Parquets")
    legacy.add_argument("release_name")
    legacy.add_argument("source_directory", type=Path)
    legacy.add_argument("--legacy-source")
    legacy.add_argument("--releases-root", default=DEFAULT_RELEASES_ROOT, type=Path)

    deploy = commands.add_parser(
        "prepare-deployment-payload", help="Build the rsconnect payload"
    )
    deploy.add_argument("--release", default="v308")

    arguments = parser.parse_args()
    if arguments.command == "prepare-deployment-payload":
        print(
            prepare_deployment_payload(DEFAULT_RELEASES_ROOT.parent, arguments.release)
        )
        return
    if arguments.command == "build-bundle":
        try:
            bundle = build_bundle(
                arguments.definition,
                DEFAULT_RELEASES_ROOT.parent.parent,
                arguments.releases_root,
            )
        except (OSError, ValueError) as error:
            parser.error(str(error))
    elif arguments.command == "build":
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
