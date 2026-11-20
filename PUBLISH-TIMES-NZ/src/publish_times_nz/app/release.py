"""The configured release used by the Explorer."""

from pathlib import Path

from publish_times_nz.app_config import configured_bundle


def labelled_file(dataset_name: str) -> Path:
    """Return a chart dataset from the configured release."""
    return configured_bundle().labelled_file(dataset_name)
