"""
This module contains a few small functions for
replicable data processing functions.

At this stage, this is just some column renaming to standardise cases.

"""

import re
import tomllib
import unicodedata

import pandas as pd

from prepare_times_nz.utilities.logger_setup import logger

# Column name tidying:


def pascal_case(name: str) -> str:
    """
    Converts a given string to PascalCase.
    Preserves all-uppercase abbreviations like 'NZ'.
    """
    parts = re.findall(r"[A-Z]?[a-z]+|[A-Z]{2,}|\d+|[A-Z]", name)
    out = []
    for word in parts:
        if word.isupper() and len(word) > 1:  # preserve acronyms
            out.append(word)
        else:
            out.append(word.capitalize())
    return "".join(out)


def rename_columns_to_pascal(df):
    """
    Rename all columns in a pandas DataFrame to PascalCase.

    This function transforms each column name in the input DataFrame by converting it
    to PascalCase (capitalizing each word and removing underscores or spaces). The
    renamed DataFrame is returned with updated column names.

    Example:
        Input columns: ['first_name', 'last_name']
        Output columns: ['FirstName', 'LastName']

    Args:
        df (pandas.DataFrame): The DataFrame whose columns will be renamed.

    Returns:
        pandas.DataFrame: A new DataFrame with PascalCase column names.
    """
    new_names = [pascal_case(col) for col in df.columns]
    mapping = dict(zip(df.columns, new_names))
    return df.rename(columns=mapping)


def remove_diacritics(text: str) -> str:
    """Strip accent marks so names are ASCII-safe for GAMS/VEDA."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def rename_eeud_techs(df, rules_file, report=False):
    """
    Apply the [[rule]] blocks from an EEUD rename TOML file to the dataframe.

    Each rule's `conditions` select rows by exact column match, and its
    `updates` overwrite columns on those rows.
    """
    with open(rules_file, "rb") as f:
        rules = tomllib.load(f)["rule"]
    for rule in rules:
        cond = pd.Series(True, index=df.index)
        if report:
            logger.info("Applying technology definition adjustment: %s", rule["Name"])
            logger.info("          Justification: %s", rule["Justification"])
        for col, val in rule["conditions"].items():
            if col not in df.columns:
                logger.warning("Column '%s' not found in DataFrame", col)
            if report:
                logger.info("          Condition: '%s' = '%s'", col, val)
            cond &= df[col] == val
        for col, val in rule["updates"].items():
            if report:
                logger.info("          Changing '%s' to '%s'", col, val)
            df.loc[cond, col] = val
    return df
