"""The stable on-disk contract for a published TIMES-NZ release."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


RELEASE_FORMAT_VERSION = 1


class BundleValidationError(ValueError):
    """Raised when a release directory does not satisfy the bundle contract."""


@dataclass(frozen=True)
class ReleaseBundle:
    """A validated release bundle and its manifest."""

    path: Path
    manifest: dict[str, object]

    @property
    def parquet_files(self) -> tuple[Path, ...]:
        """Return every Parquet file in the release, including raw results."""
        return tuple(sorted(self.path.rglob("*.parquet")))

    @property
    def scenarios(self) -> tuple[dict[str, str], ...]:
        return tuple(self.manifest["scenarios"])

    def labelled_file(self, dataset_name: str) -> Path:
        """Return one Explorer dataset beneath the conventional labelled directory."""
        if Path(dataset_name).name != dataset_name:
            raise BundleValidationError(f"Invalid labelled dataset name: {dataset_name}")
        dataset_path = self.path / "labelled" / dataset_name
        if dataset_path.suffix != ".parquet" or not dataset_path.is_file():
            raise BundleValidationError(f"Missing labelled dataset: {dataset_path}")
        return dataset_path


def load_bundle(release_path: Path) -> ReleaseBundle:
    """Load and validate the manifest and declared files for one release."""
    bundle_path = release_path / "bundle.json"
    try:
        manifest = json.loads(bundle_path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise BundleValidationError(f"Missing release manifest: {bundle_path}") from error
    except json.JSONDecodeError as error:
        raise BundleValidationError(f"Invalid release manifest: {bundle_path}") from error

    _validate_manifest(manifest)
    bundle = ReleaseBundle(release_path, manifest)
    if not bundle.parquet_files:
        raise BundleValidationError(f"Release contains no Parquet files: {release_path}")
    return bundle


def _validate_manifest(manifest: object) -> None:
    if not isinstance(manifest, dict):
        raise BundleValidationError("Release manifest must be a JSON object")
    required_keys = {
        "format_version",
        "release_name",
        "scenarios",
        "source",
        "created_at",
    }
    missing = required_keys - manifest.keys()
    if missing:
        raise BundleValidationError(
            f"Release manifest missing keys: {', '.join(sorted(missing))}"
        )
    if manifest["format_version"] != RELEASE_FORMAT_VERSION:
        raise BundleValidationError(
            f"Unsupported release format version: {manifest['format_version']}"
        )
    if not isinstance(manifest["release_name"], str) or not manifest["release_name"]:
        raise BundleValidationError(
            "Release manifest release_name must be a non-empty string"
        )
    _validate_scenarios(manifest["scenarios"])
    _validate_source(manifest["source"])
    if not isinstance(manifest["created_at"], str) or not manifest["created_at"]:
        raise BundleValidationError("Release manifest created_at must be a non-empty string")


def _validate_scenarios(scenarios: object) -> None:
    if not isinstance(scenarios, list) or not scenarios:
        raise BundleValidationError(
            "Release manifest scenarios must be a non-empty list"
        )
    scenario_ids = []
    for scenario in scenarios:
        if not isinstance(scenario, dict) or set(scenario) != {"id", "label"}:
            raise BundleValidationError("Each scenario must contain only id and label")
        if not all(isinstance(scenario[key], str) and scenario[key] for key in scenario):
            raise BundleValidationError("Scenario id and label must be non-empty strings")
        scenario_ids.append(scenario["id"])
    if len(scenario_ids) != len(set(scenario_ids)):
        raise BundleValidationError("Release manifest contains duplicate scenario IDs")


def _validate_source(source: object) -> None:
    if not isinstance(source, dict):
        raise BundleValidationError("Release manifest source must be an object")
    source_type = source.get("type")
    if source_type == "solver_runs" and isinstance(source.get("runs"), list):
        return
    if source_type == "legacy" and isinstance(source.get("legacy_source"), str):
        return
    raise BundleValidationError(
        "Release manifest source must identify solver_runs or a legacy source"
    )


