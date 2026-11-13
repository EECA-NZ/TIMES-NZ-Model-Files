"""The configured release used by the Explorer."""

from functools import lru_cache
from pathlib import Path

from publish_times_nz.release_bundle import ReleaseBundle, load_bundle


RELEASE_PATH = Path(__file__).parents[3] / "releases" / "v308"


@lru_cache(maxsize=1)
def configured_bundle() -> ReleaseBundle:
    """Load the one release explicitly selected for this app process."""
    return load_bundle(RELEASE_PATH)


def labelled_file(dataset_name: str) -> Path:
    """Return a chart dataset from the configured release."""
    return configured_bundle().labelled_file(dataset_name)
