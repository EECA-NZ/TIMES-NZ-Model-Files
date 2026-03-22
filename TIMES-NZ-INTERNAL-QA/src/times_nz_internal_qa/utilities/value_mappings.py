"""
Utilities for remapping display values without modifying source data files.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd
import polars as pl

_MAPPINGS_FILE = Path(__file__).with_name("value_mappings.json")


@lru_cache(maxsize=1)
def load_column_value_mappings() -> dict[str, dict[str, str]]:
    """
    Load the JSON-backed mapping config once per process.
    """
    with _MAPPINGS_FILE.open(encoding="utf-8") as f:
        data = json.load(f)

    mappings = data.get("column_value_mappings", {})
    return {
        str(column): {str(old): str(new) for old, new in values.items()}
        for column, values in mappings.items()
    }


def get_value_mapping(column_name: str) -> dict[str, str]:
    """
    Return the configured mapping for a column, or an empty mapping.
    """
    return load_column_value_mappings().get(column_name, {})


def remap_value(column_name: str, value: Any) -> Any:
    """
    Remap a single value for a column if a mapping exists.
    """
    if value is None:
        return value
    return get_value_mapping(column_name).get(str(value), value)


def remap_values(column_name: str, values: list[str] | tuple[str, ...]) -> list[str]:
    """
    Remap a sequence of values while preserving order.
    """
    return [remap_value(column_name, value) for value in values]


def get_choice_labels(column_name: str, values: list[str] | tuple[str, ...]) -> dict[str, str]:
    """
    Build UI choices with raw values preserved and friendly labels displayed.
    """
    return {value: remap_value(column_name, value) for value in values}


def apply_value_mappings_pl(
    df: pl.LazyFrame | pl.DataFrame,
) -> pl.LazyFrame | pl.DataFrame:
    """
    Apply configured column value remaps to a Polars frame.
    """
    if isinstance(df, pl.LazyFrame):
        column_names = set(df.collect_schema().names())
    else:
        column_names = set(df.columns)

    expressions = []
    for column_name, mapping in load_column_value_mappings().items():
        if column_name in column_names:
            expressions.append(pl.col(column_name).replace(mapping).alias(column_name))

    if not expressions:
        return df

    return df.with_columns(expressions)


def apply_value_mappings_pd(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply configured column value remaps to a pandas DataFrame.
    """
    if df.empty:
        return df

    out = df.copy()
    for column_name, mapping in load_column_value_mappings().items():
        if column_name in out.columns:
            out[column_name] = out[column_name].replace(mapping)

    return out
