"""
Executes building Veda files for new commercial techs
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pandas as pd
from prepare_times_nz.stage_0.stage_0_settings import BASE_YEAR, CAP2ACT_PJGW
from prepare_times_nz.stage_2.industry.common import (
    INDUSTRY_ASSUMPTIONS,
    INDUSTRY_CONCORDANCES,
)
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.deflator import deflate_data
from prepare_times_nz.utilities.filepaths import STAGE_4_DATA
from prepare_times_nz.utilities.logger_setup import logger

# ---------------------------------------------------------------------
# Constants & File Paths
# ---------------------------------------------------------------------
INPUT_FILE = Path(STAGE_4_DATA) / "base_year_ind" / "industry_baseyear_details.csv"
OUTPUT_LOCATION = Path(STAGE_4_DATA) / "subres_ind"
OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)

NEW_TECHS_CONFIG = INDUSTRY_ASSUMPTIONS / "future_techs/industry_tech_config.toml"
NEW_TECHS_PARAMS = INDUSTRY_ASSUMPTIONS / "future_techs/tech_parameters.csv"

SECTOR_CODES = INDUSTRY_CONCORDANCES / "sector_codes.csv"
ENDUSE_CODES = INDUSTRY_CONCORDANCES / "use_codes.csv"

# ---------------------------------------------------------------------
# Modelling Constants
# ---------------------------------------------------------------------
START = BASE_YEAR + 1
TECH_START_OVERRIDES = {"BEV": 2030, "HFCV": 2030}
ACTIVITY_UNIT = "PJ"
CAPACITY_UNIT = "GW"
AF = 0.5
VINTAGE = "YES"


# Functions


def _as_upper_list(value) -> list[str]:
    """Normalize scalar/list values to upper-case string list."""
    values = value if isinstance(value, list) else [value]
    return [str(v).strip().upper() for v in values]


def _expand_newtech_rows(item: dict) -> list[dict]:
    """
    Expand config combinations into per-process mapping rows.
    Note that replaced technology is irrelevant for Space Heating
    So it is removed here in the commodity out
    """
    tech_code = str(item["TechCode"]).strip().upper()
    sh_low_end_use = "SH_LOW"
    end_uses = _as_upper_list(item["EndUse"])
    replaced_techs = (
        _as_upper_list(item["ReplacedTechs"]) if "ReplacedTechs" in item else [None]
    )
    out = [
        {
            "TechnologyReplaced_TIMES": replaced_tech,
            "Technology_TIMES": tech_code,
            "Technology": item["Technology"],
            "TechnologyGroup": item["TechnologyGroup"],
            "EndUse_TIMES": end_use,
            "TechName": f"{sector}-{fuel}-{tech_code}-{end_use}",
            "Comm_IN": f"IND{fuel}",
            "Comm_OUT": (
                # including different commodity construction logic
                # for space heating
                f"{sector}-{end_use}"
                if end_use == sh_low_end_use
                else f"{sector}-{replaced_tech}-{end_use}"
            ),
            "Sector_TIMES": sector,
        }
        for sector in _as_upper_list(item["Sectors"])
        for fuel in _as_upper_list(item["InputFuel"])
        for replaced_tech in replaced_techs
        for end_use in end_uses
    ]
    return out


def read_newtech_config(config_file=NEW_TECHS_CONFIG):
    """
    Read new technology mapping config from TOML and return exploded mappings.
    """
    config_path = Path(config_file)
    with open(config_path, "rb") as file:
        raw_config = tomllib.load(file)

    config_items = [
        (name, item)
        for name, item in raw_config.items()
        if name.lower().startswith("newtechs")
    ]
    if not config_items:
        logger.warning("No [newtechs*] entries found in %s", config_path)
        return pd.DataFrame()

    required_fields = ["TechCode", "EndUse", "InputFuel", "Sectors"]
    rows: list[dict] = []
    for table_name, item in config_items:
        if not isinstance(item, dict) or not item:
            logger.warning(
                "Skipping [%s] in %s; section is empty or invalid",
                table_name,
                config_path,
            )
            continue
        missing_fields = [field for field in required_fields if field not in item]
        end_uses = _as_upper_list(item.get("EndUse", [])) if not missing_fields else []
        if "ReplacedTechs" not in item and any(
            end_use != "SH_LOW" for end_use in end_uses
        ):
            missing_fields.append("ReplacedTechs")
        if missing_fields:
            logger.warning(
                "Skipping [%s] in %s; missing required fields: %s",
                table_name,
                config_path,
                ", ".join(missing_fields),
            )
            continue
        rows.extend(_expand_newtech_rows(item))

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def add_parameters(df):
    """
    Combine parameter data onto main config table
    """
    params = pd.read_csv(NEW_TECHS_PARAMS)
    return df.merge(params, on="Technology_TIMES", how="left")


def get_process_declarations(df):
    """
    Identify all the unique technames in the data and create
    the FI_Process based on input
    """

    tech_defns = pd.DataFrame(
        {
            "Sets": "DMD",
            "TechName": df["TechName"].unique(),
            "Tact": ACTIVITY_UNIT,
            "Tcap": CAPACITY_UNIT,
            "TsLvl": "DAYNITE",
            "Vintage": VINTAGE,
        }
    )

    # also clarify the PCG as just whatever demand commodity
    # the thing is making
    # veda gets confused if we don't clarify this
    tech_defns["PrimaryCG"] = tech_defns["TechName"] + "_DEMO"

    return tech_defns


def get_process_params(df):
    """
    Takes our main dataframe and shapes outputs for Veda
    Includes adding a couple of additional constant fields
    """
    # main list
    param_cols = [
        "TechName",
        "Comm_IN",
        "Comm_OUT",
        "START",
        "EFF",
        "LIFE",
        "INVCOST",
        "INVCOST~2050",
        "AF",
        "CAP2ACT",
    ]
    # add additional constants
    df["START"] = (
        df["Technology_TIMES"].map(TECH_START_OVERRIDES).fillna(START).astype(int)
    )

    df["AF"] = AF
    df["CAP2ACT"] = CAP2ACT_PJGW
    # return
    return df[param_cols]


def get_process_definitions(df):
    """
    Return the labels used for the developed codes
    and include labels for explorer
    """

    definition_cols = [
        "Process",
        "CommodityIn",
        "CommodityOut",
        "Sector",
        "EnduseGroup",
        "EndUse",
        "TechnologyGroup",
        "Technology",
    ]
    # get sector and use codes
    # note the tech codes are included as part of the original config definitions
    #  (as these might be new)
    df = df.merge(pd.read_csv(SECTOR_CODES), on="Sector_TIMES", how="left")
    df = df.merge(pd.read_csv(ENDUSE_CODES), on="EndUse_TIMES", how="left")

    # some renaming
    df = df.rename(
        columns={
            "UseGroup": "EnduseGroup",
            "TechName": "Process",
            "Comm_IN": "CommodityIn",
            "Comm_OUT": "CommodityOut",
        }
    )
    df = df[definition_cols]

    return df

    #


# Main


def save_ind_data(df, name, label, output_location=OUTPUT_LOCATION):
    """save data wrapper"""
    _save_data(df, name, f"Industry new tech {label}", output_location)


def main() -> None:
    """orchestrates pipeline"""

    # build table
    df = read_newtech_config()
    df = add_parameters(df)
    variables_to_deflate = [
        col for col in ["INVCOST", "INVCOST~2050", "FIXOM"] if col in df.columns
    ]
    if variables_to_deflate:
        df = deflate_data(
            df, base_year=BASE_YEAR, variables_to_deflate=variables_to_deflate
        )
    # create outputs
    params = get_process_params(df)
    declarations = get_process_declarations(df)
    defns = get_process_definitions(df)
    # save
    save_ind_data(defns, "future_industry_process_definitions.csv", "labels")
    save_ind_data(declarations, "future_industry_processes.csv", "processes")
    save_ind_data(params, "future_industry_parameters.csv", "parameters")


if __name__ == "__main__":
    main()
