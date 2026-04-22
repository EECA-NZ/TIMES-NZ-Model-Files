"""
Reads the capacity_limits.toml config file and creates capacity growth limit user constraints
"""

import tomllib

import pandas as pd
from prepare_times_nz.stage_0.stage_0_settings import BASE_YEAR
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.filepaths import ASSUMPTIONS, STAGE_4_DATA

# Constants
CAPACITY_LIMITS_CONFIG = ASSUMPTIONS / "settings/capacity_limits.toml"
OUTPUT_PATH = STAGE_4_DATA / "sys_settings"
PSET_FIELD_MAP = {
    "pset_set": "Pset_Set",
    "pset_pn": "Pset_PN",
    "pset_ci": "Pset_CI",
    "pset_co": "Pset_CO",
}


def define_default_uc_line():
    """
    Simple full defaults for user constraint.
    Note we set these to RHS so values are more intuitive

    See: https://forum.kanors-emr.org/showthread.php?tid=1196
    """

    return pd.DataFrame(
        [
            {
                "UC_N": "",
                "Pset_Set": "",
                "Pset_PN": "",
                "Pset_CI": "",
                "Pset_CO": "",
                "UC_ATTR~RHS": "CAP,GROWTH",
                "Year": BASE_YEAR,
                "LimType": "UP",
                "UC_CAP": 1,
                "UC_CAP~RHS": 1,
                "UC_RHSRTS": 0,
                "UC_RHSRTS~0": 5,
            }
        ]
    )


def read_capacity_config(config_file=CAPACITY_LIMITS_CONFIG):
    """
    Read capacity limit config from TOML and validate each section.

    Required fields in each TOML section:
    - at least one Pset_* field
    - GrowthLimit
    - Description

    Optional fields:
    - SeedValue

    Returns:
    - dict keyed by constraint name, with normalized Pset field names
    """
    with open(config_file, "rb") as file:
        raw_config = tomllib.load(file)

    if not raw_config:
        return {}

    validated_config = {}

    for constraint_name, item in raw_config.items():
        if not isinstance(item, dict) or not item:
            continue

        normalized_pset_fields = {
            canonical_name: item[key]
            for key in item
            if (canonical_name := PSET_FIELD_MAP.get(key.lower())) is not None
        }
        missing_fields = [
            field for field in ["GrowthLimit", "Description"] if field not in item
        ]
        if not normalized_pset_fields:
            missing_fields.append("at least one Pset_* field")
        if missing_fields:
            raise ValueError(
                f"[{constraint_name}] is missing required fields: " f"{missing_fields}"
            )

        normalized_item = {
            key: value
            for key, value in item.items()
            if key.lower() not in PSET_FIELD_MAP
        }
        normalized_item.update(normalized_pset_fields)
        validated_config[constraint_name] = normalized_item

    return validated_config


def create_uc_table(config_data=None):
    """
    Takes the config file and adds values to the UC table

    UC_N should become UC_[entryname]

    If a seed value is provided, this is inserted as UC_RHSRTS (but as a negative)
    """
    if config_data is None:
        config_data = read_capacity_config()

    empty_df = define_default_uc_line().iloc[0:0].copy()
    if not config_data:
        return empty_df

    default_row = define_default_uc_line().iloc[0].to_dict()
    rows = []

    for constraint_name, item in config_data.items():
        row = default_row.copy()
        row["UC_N"] = f"UC_{constraint_name}"
        row["UC_CAP~RHS"] = 1 + item["GrowthLimit"]
        row["UC_Desc"] = item["Description"]

        for field in ["Pset_Set", "Pset_PN", "Pset_CI", "Pset_CO"]:
            if field in item:
                row[field] = item[field]

        if "SeedValue" in item:
            row["UC_RHSRTS"] = item["SeedValue"]

        rows.append(row)

    return pd.DataFrame(rows)


def main():
    """entrypoint"""
    cfg = read_capacity_config()
    cap_limit_df = create_uc_table(cfg)
    _save_data(
        cap_limit_df, "capacity_limits_uc.csv", "Capacity user constraints", OUTPUT_PATH
    )


if __name__ == "__main__":
    main()
