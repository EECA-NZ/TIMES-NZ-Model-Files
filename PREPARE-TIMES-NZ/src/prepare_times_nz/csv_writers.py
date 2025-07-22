"""
Module to house code for interacting with CSV files

This module provides functionality to save a pandas
DataFrame to a CSV file, logging the action with a
provided logger. It is designed to be used in data
preparation workflows, particularly for the Times
NZ project.
"""

from logging import Logger, getLogger
from pathlib import Path

import pandas as pd
from prepare_times_nz.logger_setup import blue_text

_default_logger = getLogger(__name__)


def save_dataframe_to_csv(
    df: pd.DataFrame,
    directory: str | Path,
    filename: str | Path,
    logger: Logger | None = None,
    label: str = "output",
) -> None:
    """
    Write *df* to *directory/filename* and emit a nicely-coloured INFO log.

    Parameters
    ----------
    df
        The DataFrame to write.
    directory
        Folder to save into (created if it doesn’t exist).
    filename
        Name of the CSV file (with or without “.csv”).
    logger
        Optional :pyclass:`logging.Logger`.  Falls back to a module logger
        so callers don’t *have* to pass one.
    label
        Text shown in the log message (“output”, “check file”, …).
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)

    # Ensure “filename.csv”
    filename = Path(filename)
    if filename.suffix.lower() != ".csv":
        filename = filename.with_suffix(".csv")

    full_path: Path = directory / filename
    (logger or _default_logger).info("Saving %s:\n%s", label, blue_text(str(full_path)))
    df.to_csv(full_path, index=False)
