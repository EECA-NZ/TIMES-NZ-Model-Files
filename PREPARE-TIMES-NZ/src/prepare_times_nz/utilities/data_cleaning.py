"""
This module contains a few small functions for
replicable data processing functions.

At this stage, this is just some column renaming to standardise cases.

"""

import re

# Column name tidying:


def pascal_case(name: str) -> str:
    """
    Converts a given string to PascalCase format.
    Splits the input string by non-word characters and camelCase boundaries,
    then capitalizes each part and concatenates them.
    Args:
        name (str): The input string to convert.
    Returns:
        str: The PascalCase formatted string.
    """
    # Split by non-word characters and camelCase boundaries
    parts = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)", name)
    return "".join(word.capitalize() for word in parts)


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
