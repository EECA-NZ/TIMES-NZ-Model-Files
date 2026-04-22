"""
Writes common constraint inputs shared across stage 4 outputs.

- Banned base-year technologies
- Capacity growth limit user constraints
"""

from pathlib import Path

import pandas as pd
from prepare_times_nz.stage_4.baseyear.declare_banned_techs import (
    create_ban_table,
    register_codes_to_ban,
)
from prepare_times_nz.stage_4.capacity_limits import (
    create_uc_table,
    read_capacity_config,
)
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.filepaths import (
    ASSUMPTIONS,
    PREP_LOCATION,
    STAGE_4_DATA,
)

INPUT_DIRECTORY = ASSUMPTIONS / "settings"
OUTPUT_DIRECTORY = STAGE_4_DATA / "sys_settings"
DOC_TABLE_DIRECTORY = (
    PREP_LOCATION / "docs/source/model_methodology/other_constraints/tables"
)

BANNED_TECHS_INPUT = INPUT_DIRECTORY / "banned_techs.csv"
BANNED_TECHS_OUTPUT = OUTPUT_DIRECTORY / "banned_techs.csv"
BANNED_TECHS_DOC_OUTPUT = DOC_TABLE_DIRECTORY / "banned_techs.csv"

CAPACITY_LIMITS_INPUT = INPUT_DIRECTORY / "capacity_limits.toml"
CAPACITY_LIMITS_OUTPUT = OUTPUT_DIRECTORY / "capacity_limits_uc.csv"
CAPACITY_LIMITS_DOC_OUTPUT = DOC_TABLE_DIRECTORY / "capacity_limits_uc.csv"


def save_dataframe(df, output_path: Path, label: str) -> None:
    """Save a generated artefact to the common constraints output directory."""
    _save_data(df, output_path.name, label, output_path.parent)


def build_banned_techs_df():
    """Build the banned base-year technologies import table."""
    return create_ban_table(register_codes_to_ban(BANNED_TECHS_INPUT))


def build_capacity_limits_df():
    """Build the capacity growth limit user constraint table."""
    return create_uc_table(read_capacity_config(CAPACITY_LIMITS_INPUT))


def build_banned_techs_doc_df():
    """Build the documentation table for banned base-year technologies."""
    df = pd.read_csv(BANNED_TECHS_INPUT)
    df["Code"] = df["Code"].astype(str).str.replace("*", r"\*", regex=False)
    return df


def escape_markdown_asterisks(value):
    """Escape wildcard asterisks so docs tables render literal values."""
    if pd.isna(value):
        return value
    return str(value).replace("*", r"\*")


def build_capacity_limits_doc_df():
    """Build the documentation table for capacity growth limit assumptions."""
    config_data = read_capacity_config(CAPACITY_LIMITS_INPUT)
    rows = []

    for item in config_data.values():
        seed_value = item.get("SeedValue", "")
        additional_capacity = ""
        if seed_value != "" and not pd.isna(seed_value):
            # Note: almost all techs are in GW but this is fragile to edge cases
            # if we are adding this feature for PJa or vehicle techs will need to
            # make more sophisticated or will report wrong
            additional_capacity = f"{seed_value * 1000:.0f}MW"

        row = {
            "Description": item["Description"],
            "Annual growth limit": f"{item['GrowthLimit']:.0%}",
            "Additional capacity": additional_capacity,
            # "Process Set": item.get("Pset_Set", ""),
            "Process name": escape_markdown_asterisks(item.get("Pset_PN", "")),
            # "Commodity In": item.get("Pset_CI", ""),
            # "Commodity Out": item.get("Pset_CO", ""),
        }
        rows.append(row)

    return pd.DataFrame(rows)


def save_banned_techs(df) -> None:
    """Create and save the banned base-year technologies artefact."""
    save_dataframe(
        df,
        BANNED_TECHS_OUTPUT,
        "Saving banned base year techs",
    )


def save_capacity_limits(df) -> None:
    """Create and save the capacity growth limit user constraints artefact."""
    save_dataframe(
        df,
        CAPACITY_LIMITS_OUTPUT,
        "Saving capacity user constraints",
    )


def save_banned_techs_doc_table() -> None:
    """Save the banned base-year technologies artefact to the docs tables directory."""
    doc_df = build_banned_techs_doc_df()
    save_dataframe(
        doc_df,
        BANNED_TECHS_DOC_OUTPUT,
        "Saving docs banned techs",
    )


def save_capacity_limits_doc_table() -> None:
    """Save the capacity growth limit artefact to the docs tables directory."""
    doc_df = build_capacity_limits_doc_df()
    save_dataframe(
        doc_df,
        CAPACITY_LIMITS_DOC_OUTPUT,
        "Saving docs capacity limits",
    )


def main():
    """Entrypoint."""
    banned_techs_df = build_banned_techs_df()
    capacity_limits_df = build_capacity_limits_df()

    save_banned_techs(banned_techs_df)
    save_banned_techs_doc_table()
    save_capacity_limits(capacity_limits_df)
    save_capacity_limits_doc_table()


if __name__ == "__main__":
    main()
