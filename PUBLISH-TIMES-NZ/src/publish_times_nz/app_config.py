"""Read the Explorer's selected release from the PUBLISH root."""

import tomllib
from functools import lru_cache
from pathlib import Path

from publish_times_nz.release_bundle import ReleaseBundle, load_bundle

PUBLISH_ROOT = Path(__file__).parents[2]


@lru_cache(maxsize=1)
def configured_bundle() -> ReleaseBundle:
    """Load the one release explicitly selected for this app process."""
    return load_bundle(configured_release_path(PUBLISH_ROOT))


def load_explorer_config(publish_root: Path) -> dict:
    """Read release selection and optional display labels from one config."""
    with (publish_root / "explorer_bundle.toml").open("rb") as source:
        return tomllib.load(source)


def configured_release_path(
    publish_root: Path, release_name: str | None = None
) -> Path:
    """Resolve the configured release, allowing a deployment-only override."""
    if release_name is None:
        release_name = load_explorer_config(publish_root).get("release")
    if (
        not isinstance(release_name, str)
        or release_name in {"", ".", ".."}
        or Path(release_name).name != release_name
    ):
        raise ValueError("Explorer release must be a folder name under releases/")
    return publish_root / "releases" / release_name
