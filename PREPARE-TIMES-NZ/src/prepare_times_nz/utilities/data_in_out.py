"""
Standardised helper functions for saving/loading data

Could wrap this in more comprehensive logging if we wanted!

Long term, ideally every in/out would be wrapped in here
and the script's inputs and outputs can be logged
This will help us trace how things flow through later.
For now, just standard helpers to be used elsewhere
"""

from pathlib import Path

from prepare_times_nz.utilities.logger_setup import blue_text, logger


def _save_data(df, name, label, filepath: Path):
    """Save DataFrame output to the output location and print to console"""
    filepath.mkdir(parents=True, exist_ok=True)
    filename = filepath / name
    logger.info("%s: %s", label, blue_text(filename))
    df.to_csv(filename, index=False, encoding="utf-8-sig")
