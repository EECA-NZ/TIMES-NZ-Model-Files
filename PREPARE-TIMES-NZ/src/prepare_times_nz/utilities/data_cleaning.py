"""
This module contains a few small functions for
replicable data processing functions.

At this stage, this is just some column renaming to standardise cases.

"""

import re
import unicodedata

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
