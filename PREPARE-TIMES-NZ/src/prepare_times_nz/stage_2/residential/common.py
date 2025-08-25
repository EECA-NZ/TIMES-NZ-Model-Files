"""
A common area for all filepaths and functions common to
 residential baseyear processing submodules


"""

from pathlib import Path

from prepare_times_nz.utilities.filepaths import (
    ASSUMPTIONS,
    CONCORDANCES,
    STAGE_1_DATA,
    STAGE_2_DATA,
)
from prepare_times_nz.utilities.logger_setup import blue_text, logger

# Constants ------------------------------------------------
BASE_YEAR = 2023
RUN_TESTS = False
CAP2ACT = 31.536

# Filepaths ------------------------------------------------


RESIDENTIAL_ASSUMPTIONS = ASSUMPTIONS / "residential"
RESIDENTIAL_DATA_DIR = STAGE_2_DATA / "residential"
CHECKS_DIR = RESIDENTIAL_DATA_DIR / "checks"
PREPROCESSING_DIR = RESIDENTIAL_DATA_DIR / "preprocessing"


# Functions ------------------------------------------------


def _save_data(df, name, label, dir: Path):
    """Save DataFrame output to the output location."""
    dir.mkdir(parents=True, exist_ok=True)
    filename = f"{dir}/{name}"
    logger.info("Saving %s:\n%s", label, blue_text(filename))
    df.to_csv(filename, index=False, encoding="utf-8-sig")


def save_output(df, name, label, dir=RESIDENTIAL_DATA_DIR):
    """Save DataFrame output to the output location."""
    _save_data(df=df, name=name, label=label, dir=dir)


def save_preprocessing(df, name, label, dir=PREPROCESSING_DIR):
    """Save DataFrame output to the output location."""
    _save_data(df=df, name=name, label=label, dir=dir)


def save_checks(df, name, label, dir=CHECKS_DIR):
    """Save DataFrame output to the checks location."""
    _save_data(df=df, name=name, label=label, dir=dir)
