#!/usr/bin/env python3
"""
Stage 4 – VEDA-format builders for the transport (TRA) sector.

• Reads stage 2 base-year demand CSV
• Builds commodity / process / parameter tables
• Writes them to   DATA_INTERMEDIATE/stage_4_veda_format/base_year_tra
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
import pandas as pd
from prepare_times_nz.utilities.filepaths import (
    STAGE_2_DATA,
    STAGE_3_DATA,
    STAGE_4_DATA,
)

# ──────────────────────────────────────────────────────────────── #
# Logging
# ──────────────────────────────────────────────────────────────── #
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ──────────────────────────────────────────────────────────────── #
# Constants - all paths use pathlib for cross-platform consistency
# ──────────────────────────────────────────────────────────────── #

INPUT_LOCATION = Path(STAGE_2_DATA) / "transport"
SCENARIO_LOCATION = Path(STAGE_3_DATA) / "transport"

OUTPUT_LOCATION = Path(STAGE_4_DATA) / "base_year_tra"
OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)

TRA_FILE: Path = INPUT_LOCATION / "transport_demand_2023.csv"

# ────────────────────────────────────────────────────────────────
# Constants
# ────────────────────────────────────────────────────────────────
FUEL_TO_COMM = {
    "PET": "TRAPET",
    "DSL": "TRADSL",
    "LPG": "TRALPG",
    "ELC": "TRAELC",
    "H2": "TRAH2R",
}

SPECIAL_COMM_IN: dict[str, list[str]] = {
    "T_F_DSHIPP15": ["TRAFOL"],
    "T_F_ISHIPP15": ["TRAFOL"],
    "T_O_FuelJet": ["TRAJet"],
    "T_O_FuelJet_Int": ["TRAJet"],
    "T_R_Rail15": ["TRADSL", "TRAELC"],
    "T_P_Rail15": ["TRAELC", "TRADSL"],
}

COMM_TO_VEHICLE = {
    "T_P_Car": "LPV",
    "T_C_Car": "LCV",
    "T_P_Mcy": "Motorcycle",
    "T_P_Bus": "Bus",
    "T_F_LTrk": "Light Truck",
    "T_F_MTrk": "Medium Truck",
    "T_F_HTrk": "Heavy Truck",
    "T_F_Rail": "Rail Freight",
    "T_P_Rail": "Passenger Rail",
    "T_F_DSHIP": "Domestic Shipping",
    "T_F_ISHIP": "International Shipping",
    "T_O_JET": "Domestic Aviation",
    "T_O_JET_Int": "International Aviation",
}

VAR_LIST = [
    "efficiency",
    "life(years)",
    "vktvalue",
    "pjvalue",
    "ACT_BND_0",
    "Cap2Act",
    "annual_utilisation_rate",
    "cost_2023_nzd",
    "operation_cost_2023_nzd",
    "vehicle_count",
    "fuelshare",
]
VAR_RENAME = {
    "efficiency": "EFF",
    "life(years)": "LIFE",
    "vktvalue": "ACT_BND~2023",
    "pjvalue": "ACT_BND~2023",
    "ACT_BND_0": "ACT_BND~0",
    "Cap2Act": "CAP2ACT",
    "annual_utilisation_rate": "AFA",
    "cost_2023_nzd": "INVCOST",
    "operation_cost_2023_nzd": "FIXOM",
    "vehicle_count": "PRC_resid~2023",
    "fuelshare": "Share",
}

START = 2025
INVCOST_0 = 5
SCENARIO = ["Traditional", "Transformation"]


# # -----------------------------------------------------------------------------
# # GENERIC HELPERS
# # -----------------------------------------------------------------------------
def strip_level(name: str) -> str:
    """Removes the demand level suffix ('_LOW', '_MED', '_HIGH')
    from a technology name."""
    name_up = name.upper()
    for suf in ("_LOW", "_MED", "_HIGH"):
        if name_up.endswith(suf):
            return name[: -len(suf)]
    return name


def extract_tertile(tech: str) -> int:
    """Extracts the tertile index from a technology name based on its level suffix."""
    if tech.endswith("_LOW"):
        return 0
    if tech.endswith("_MED"):
        return 1
    if tech.endswith("_HIGH"):
        return 2
    return 0  # default or exception


def get_base_name(tech_name, base_list):
    """Matches a stripped technology name against a base name list."""
    base = strip_level(tech_name)
    for b in base_list:
        if base == b:
            return b
    return base


def assign_tcap(base):
    """Assigns the appropriate TIMES capacity unit based on the base technology name."""
    if base in {
        "T_F_DSHIPP15",
        "T_F_ISHIPP15",
        "T_O_FuelJet",
        "T_O_FuelJet_Int",
        "T_R_Rail15",
        "T_P_Rail15",
    }:
        return "PJa"
    if base in {
        "T_P_CICEPET15",
        "T_P_CICEDSL15",
        "T_P_CBEVNEW15",
        "T_P_CBEVUSD15",
        "T_P_CICELPG15",
        "T_P_CHYBPET15",
        "T_P_CPHEVPET15",
        "T_C_CICEPET15",
        "T_C_CICEDSL15",
        "T_C_CBEVNEW15",
        "T_C_CICELPG15",
        "T_C_CHYBPET15",
    }:
        return "000cars"
    if base in {"T_P_MICEPET15", "T_P_MBEVELC15"}:
        return "000mcy"
    if base in {"T_P_BICEPET15", "T_P_BICEDSL15", "T_P_BICELPG15", "T_P_BBEVELC15"}:
        return "000busses"
    if base in {
        "T_F_LTICEPET15",
        "T_F_LTICEDSL15",
        "T_F_LTBEVELC15",
        "T_F_MTICEDSL15",
        "T_F_MTBEVELC15",
        "T_F_HTICEDSL15",
        "T_F_HTBEVELC15",
    }:
        return "000trucks"
    return None


def first_match(name: str, bases: Sequence[str]) -> str:
    """Return the first base string that matches *name*, else the stripped name."""
    stem = strip_level(name)
    return next((b for b in bases if stem.startswith(b)), stem)


def load_var_tables(demand: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Return lower-cased lookup tables for every variable in VAR_LIST."""
    tbls: dict[str, pd.DataFrame] = {}
    for var in VAR_LIST:
        sub = (
            demand.loc[demand["variable"] == var]
            .drop(columns="variable")
            .assign(
                **{
                    c: lambda d, col=c: d[col].str.strip().str.lower()
                    for c in ("vehicletype", "fueltype", "technology", "region")
                }
            )
        )
        tbls[var] = sub
    return tbls


# pylint: disable=too-many-return-statements
def comm_out_for_tech(base: str) -> str | None:
    """Map Tech base name → Comm-Out code."""
    # pylint: disable=invalid-name
    PREFIX = {
        "T_P_C": "T_P_Car",
        "T_C_C": "T_C_Car",
        "T_P_M": "T_P_Mcy",
        "T_P_B": "T_P_Bus",
        "T_F_LT": "T_F_LTrk",
        "T_F_MT": "T_F_MTrk",
        "T_F_HT": "T_F_HTrk",
    }

    base_up = base.upper()
    if "FUELJET_INT" in base_up:
        return "T_O_JET_Int"
    if "FUELJET" in base_up:
        return "T_O_JET"

    for pre, out in PREFIX.items():
        if base.startswith(pre):
            return out

    if "T_R_RAIL" in base_up:
        return "T_F_Rail"
    if "T_P_RAIL" in base_up:
        return "T_P_Rail"
    if "DSHIPP" in base_up:
        return "T_F_DSHIP"
    if "ISHIPP" in base_up:
        return "T_F_ISHIP"
    return None


def infer_comm_in(name: str) -> str | None:
    """Infer Comm-In from PET/DSL/LPG/ELC/H2 in tech name."""
    up = name.upper()
    if "BEV" in up:  # catch BEV techs
        return "TRAELC"
    return next((v for k, v in FUEL_TO_COMM.items() if k in up), None)


# pylint: disable=too-many-branches
def parse_attrs(
    tech: str, comm_out: str, comm_in: str
) -> tuple[str | None, str | None, str | None]:
    """Return (vehicle, fuel, technology)."""
    up = tech.upper()
    vehicle = COMM_TO_VEHICLE.get(comm_out)

    # fuel
    if comm_in == "TRAELC" or "ELC" in up:
        fuel = "Electricity"
    elif comm_in == "TRADSL" or "DSL" in up:
        fuel = "Diesel"
    elif "PET" in up:
        fuel = "Petrol"
    elif "LPG" in up:
        fuel = "LPG"
    elif "H2" in up:
        fuel = "Hydrogen"
    elif comm_out in ("T_F_DSHIP", "T_F_ISHIP"):
        fuel = "Fuel Oil"
    elif "JET" in up or comm_out.startswith("T_O_JET"):
        fuel = "Av. Fuel/Kero"
    else:
        fuel = None

    # tech-type
    if "ICE" in up:
        ttype = "ICE"
    elif "BEV" in up:
        ttype = "BEV"
    elif "PHEV" in up:
        ttype = "PHEV"
    elif "HYB" in up:
        ttype = "ICE Hybrid"
    elif "H2R" in up:
        ttype = "H2R"
    elif comm_out.startswith("T_O_JET"):
        ttype = "Turbine Engine"
    elif comm_out in ("T_F_DSHIP", "T_F_ISHIP") or (
        comm_out.endswith("_Rail") and fuel == "Diesel"
    ):
        ttype = "ICE"
    elif comm_out.endswith("_Rail") and fuel == "Electricity":
        ttype = "Electric Motor"
    else:
        ttype = None

    return vehicle, fuel, ttype


# -----------------------------------------------------------------------------
# BUILDERS – simple ones kept verbatim (only spacing/PEP-8 tweaks)
# -----------------------------------------------------------------------------
def create_fuel_commodity_df(cfg):
    """Creates a DataFrame defining fuel commodities."""
    comm_names = [
        "TRANGA",
        "TRABIL",
        "TRALPG",
        "TRAPET",
        "TRADSL",
        "TRAJET",
        "TRAH2R",
        "TRAELC",
        "TRAFOL",
        "TRACO2",
    ]
    regions = ["NI", "SI"]
    df = pd.DataFrame(
        [(comm, region) for comm in comm_names for region in regions],
        columns=["CommName", "Region"],
    )
    df["Csets"] = df["CommName"].apply(lambda x: "ENV" if x == "TRACO2" else "NRG")
    df["Unit"] = df["CommName"].apply(lambda x: "Kt" if x == "TRACO2" else "PJ")
    df["LimType"] = df["CommName"].apply(lambda x: "" if x == "TRACO2" else "FX")
    df["CTSLvl"] = df["CommName"].apply(
        lambda x: "DAYNITE" if x in ["TRAH2R", "TRAELC"] else "ANNUAL"
    )
    df["Ctype"] = df["CommName"].apply(lambda x: "ELC" if x == "TRAELC" else "")
    final_column_order = cfg["Columns"]
    return df[final_column_order]


def create_fuel_process_df(cfg):
    """Creates a DataFrame defining fuel processes."""
    tech_names = [
        "FTE_TRANGA",
        "FTE_TRABIL",
        "FTE_TRALPG",
        "FTE_TRAPET",
        "FTE_TRADSL",
        "FTE_TRAJET",
        "FTE_TRAH2R",
        "G_ELC_T_00",
        "FTE_TRAFOL",
    ]
    regions = ["NI", "SI"]
    df = pd.DataFrame(
        [(tech, region) for tech in tech_names for region in regions],
        columns=["TechName", "Region"],
    )
    df["Sets"] = ""
    df.loc[0, "Sets"] = "DISTR"
    df["Tact"] = "PJ"
    df["Tcap"] = df["TechName"].apply(
        lambda x: "GW" if x in ["FTE_TRAH2R", "G_ELC_T_00"] else "PJa"
    )
    df["Tslvl"] = df["TechName"].apply(
        lambda x: "DAYNITE" if x in ["FTE_TRAH2R", "G_ELC_T_00"] else ""
    )
    final_column_order = cfg["Columns"]
    return df[final_column_order]


def create_commodity_df(cfg):
    """Creates a DataFrame defining transport commodities."""
    comm_names = [
        "T_P_Car",
        "T_C_Car",
        "T_P_Mcy",
        "T_P_Bus",
        "T_F_LTrk",
        "T_F_MTrk",
        "T_F_HTrk",
        "T_F_Rail",
        "T_P_Rail",
        "T_F_DSHIP",
        "T_F_ISHIP",
        "T_O_JET",
        "T_O_JET_Int",
        "H2R",
    ]
    regions = ["NI", "SI"]
    df = pd.DataFrame(
        [(comm, region) for comm in comm_names for region in regions],
        columns=["CommName", "Region"],
    )
    df["Csets"] = df["CommName"].apply(lambda x: "NRG" if x == "H2R" else "DEM")
    df["Unit"] = df["CommName"].apply(
        lambda x: (
            "BVkm"
            if x
            in [
                "T_P_Car",
                "T_C_Car",
                "T_P_Mcy",
                "T_P_Bus",
                "T_F_LTrk",
                "T_F_MTrk",
                "T_F_HTrk",
            ]
            else "PJ"
        )
    )
    df["LimType"] = df["CommName"].apply(lambda x: "FX" if x == "H2R" else "")
    final_column_order = cfg["Columns"]
    return df[final_column_order]


def create_process_df(cfg):
    """Creates a DataFrame defining base year technologies."""
    tech_names_base = [
        "T_P_CICEPET15",
        "T_P_CICEDSL15",
        "T_P_CBEVNEW15",
        "T_P_CBEVUSD15",
        "T_P_CICELPG15",
        "T_P_CHYBPET15",
        "T_P_CPHEVPET15",
        "T_C_CICEPET15",
        "T_C_CICEDSL15",
        "T_C_CBEVNEW15",
        "T_C_CICELPG15",
        "T_C_CHYBPET15",
        "T_P_MICEPET15",
        "T_P_MBEVELC15",
        "T_P_BICEPET15",
        "T_P_BICEDSL15",
        "T_P_BICELPG15",
        "T_P_BBEVELC15",
        "T_F_LTICEPET15",
        "T_F_LTICEDSL15",
        "T_F_LTBEVELC15",
        "T_F_MTICEDSL15",
        "T_F_MTBEVELC15",
        "T_F_HTICEDSL15",
        "T_F_HTBEVELC15",
        "T_F_DSHIPP15",
        "T_F_ISHIPP15",
        "T_O_FuelJet",
        "T_O_FuelJet_Int",
        "T_R_Rail15",
        "T_P_Rail15",
    ]
    regions = ["NI", "SI"]
    exceptions = {
        "T_F_DSHIPP15",
        "T_F_ISHIPP15",
        "T_O_FuelJet",
        "T_O_FuelJet_Int",
        "T_R_Rail15",
        "T_P_Rail15",
    }
    tech_names = [
        f"{name}_{level}" if name not in exceptions else name
        for name in tech_names_base
        for level in (["LOW", "MED", "HIGH"] if name not in exceptions else [""])
    ]
    df = pd.DataFrame(
        [(tech, region) for tech in tech_names for region in regions],
        columns=["TechName", "Region"],
    )
    df["Sets"] = "DMD"
    df["Tact"] = df["TechName"].apply(
        lambda x: "PJ" if get_base_name(x, tech_names_base) in exceptions else "BVkm"
    )
    df["Tcap"] = df["TechName"].apply(
        lambda x: assign_tcap(get_base_name(x, tech_names_base))
    )
    final_column_order = cfg["Columns"]
    return df[final_column_order]


# pylint: disable=too-many-locals
def create_fuel_process_parameters_df(cfg):
    """Constructs a DataFrame of fuel process parameters for transport technologies.

    This function generates process parameter rows for transport fuel technologies
    based on the output of `create_fuel_process_df`, and maps each technology to
    its associated input and output commodities."""
    tech_df = create_fuel_process_df({"Columns": ["TechName", "Region"]})
    expanded_comm_in = {
        "FTE_TRADSL": ["DSL", "BDSL", "DID"],
        "FTE_TRAJET": ["JET", "DIJ"],
    }
    rows = []
    for _, row in tech_df.iterrows():
        tech = row["TechName"]
        region = row["Region"]
        comm_out = tech.replace("FTE_", "").replace("G_ELC_T_00", "TRAELC")
        comm_in_list = expanded_comm_in.get(
            tech, [comm_out.replace("TRA", "").replace("TRAELC", "ELCD")]
        )
        for comm_in in comm_in_list:
            share_i_up = share_i_up_2025 = share_i_up_2060 = np.nan
            eff = 1
            life = 60
            fixom = varom = flo_deliv = np.nan
            if "H2R" in tech:
                eff = 0.37
                life = 20
                fixom = 100.40972
            if comm_in in ["NGA", "LPG"]:
                varom = 4.946
            elif comm_in in ["PET", "DSL"]:
                varom = 0.92
            elif comm_in in ["DIJ", "DID"]:
                flo_deliv = 2.4
            if comm_in in ["DSL", "DID"]:
                share_i_up = share_i_up_2025 = share_i_up_2060 = 1
            elif comm_in == "BDSL":
                share_i_up = share_i_up_2025 = share_i_up_2060 = 0.07
            rows.append(
                {
                    "TechName": tech,
                    "Region": region,
                    "Comm-In": comm_in,
                    "Comm-Out": comm_out,
                    "Share-I~UP": share_i_up,
                    "Share-I~UP~2025": share_i_up_2025,
                    "Share-I~UP~2060": share_i_up_2060,
                    "EFF": eff,
                    "Life": life,
                    "FIXOM": fixom,
                    "VAROM": varom,
                    "FLO_DELIV": flo_deliv,
                }
            )
    final_column_order = cfg["Columns"]
    return pd.DataFrame(rows)[final_column_order]


# -----------------------------------------------------------------------------
# COMPLEX builder (process parameters)
# -----------------------------------------------------------------------------
def create_process_parameters_df(cfg: Mapping[str, list[str]]) -> pd.DataFrame:
    """Main Process-Parameters table (uses VAR_LIST)."""
    demand = pd.read_csv(TRA_FILE)
    var_tbls = load_var_tables(demand)
    tech_df = create_process_df({"Columns": ["TechName", "Region"]})

    # Comm-Out map
    comm_out_map = {t: comm_out_for_tech(strip_level(t)) for t in tech_df["TechName"]}
    rows: list[dict[str, object]] = []

    for tech, region in tech_df[["TechName", "Region"]].itertuples(index=False):
        comm_out = comm_out_map.get(tech)
        if comm_out is None:
            continue

        # 1) specials first
        comm_ins = next(
            (lst for key, lst in SPECIAL_COMM_IN.items() if key in tech), None
        )

        # 2) PHEV: allow multiple fuels (liquid + electricity) for one TechName
        if comm_ins is None and "PHEV" in tech.upper():
            up = tech.upper()
            fuels = []
            if "PET" in up:
                fuels.append("TRAPET")  # petrol
            if "DSL" in up:
                fuels.append("TRADSL")  # diesel PHEV variants, if any
            fuels.append("TRAELC")  # electricity for all PHEVs
            comm_ins = fuels

        # 3) default inference for everything else
        if comm_ins is None:
            ci = infer_comm_in(tech)
            comm_ins = [ci] if ci else []

        for comm_in in comm_ins:
            veh, fuel, ttype = parse_attrs(tech, comm_out, comm_in)
            row = {
                "TechName": tech,
                "Region": region,
                "Comm-In": comm_in,
                "Comm-Out": comm_out,
            }

            # ADD THIS HERE
            is_special = any(key in tech for key in SPECIAL_COMM_IN)

            for var in VAR_LIST:
                out = VAR_RENAME[var]

                # Skip pjvalue/vktvalue based on tech type
                if var == "pjvalue" and not is_special:
                    continue
                if var == "vktvalue" and is_special:
                    continue

                if None in (veh, fuel, ttype):
                    row[out] = None
                    continue

                tbl = var_tbls[var]

                if is_special:
                    # Match without tertile
                    hit = tbl[
                        (tbl["vehicletype"] == veh.lower())
                        & (tbl["fueltype"] == fuel.lower())
                        & (tbl["technology"] == ttype.lower())
                        & (tbl["region"] == region.lower())
                    ]
                else:
                    tech_tertile = extract_tertile(tech)
                    hit = tbl[
                        (tbl["vehicletype"] == veh.lower())
                        & (tbl["fueltype"] == fuel.lower())
                        & (tbl["technology"] == ttype.lower())
                        & (tbl["region"] == region.lower())
                        & (tbl["tertile"] == tech_tertile)
                    ]

                row[out] = hit["value"].iloc[0] if not hit.empty else None
            # Append the row after it's fully built
            rows.append(row)

    df = pd.DataFrame(rows)
    # Add empty columns if missing
    for col in cfg["Columns"]:
        if col not in df.columns:
            df[col] = None  # or np.nan
    return df[cfg["Columns"]]


def creat_process_paramereters2_df(cfg: Mapping[str, list[str]]) -> pd.DataFrame:
    """Sums up ACT_BND~2023 based on Comm-Out and Region"""
    # Build the process parameters table using the existing function,
    # selecting only the needed columns.
    base_df = create_process_parameters_df(
        {"Columns": ["TechName", "Region", "Comm-In", "Comm-Out", "ACT_BND~2023"]}
    )
    # Group by Region and Comm-Out and sum the ACT_BND~2023 values.
    agg_df = base_df.groupby(["Region", "Comm-Out"], as_index=False)[
        "ACT_BND~2023"
    ].sum()
    # Rename columns to match the desired output: Region, CommName, and 2023.
    agg_df = agg_df.rename(columns={"Comm-Out": "CommName", "ACT_BND~2023": "2023"})
    # Return the dataframe with columns in the order specified by the config.
    return agg_df[cfg["Columns"]]


def emission_factors_df(cfg: Mapping[str, list[str]]) -> pd.DataFrame:
    """Returns emission factors for selected transport fuels."""

    data = {
        "CommName": ["TRACO2"],
        "TRALPG": [61.04],
        "TRAPET": [68.79],
        "TRADSL": [69.63],
        "TRAJET": [67.76],
        "TRAFOL": [75.36],
    }

    emi_df = pd.DataFrame(data).set_index("CommName")
    return emi_df.reset_index()[cfg["Columns"]]


# -----------------------------------------------------------------------------
# MAIN – orchestrate every builder & write CSVs
# -----------------------------------------------------------------------------
def main() -> None:
    """Generates and exports TIMES-NZ transport sector definition and parameter tables.

    This function sequentially runs a set of table-builder functions
    (e.g., fuel definitions, process definitions, technical parameters)
    and writes the resulting DataFrames to CSV files using standardized
    output filenames. Each builder function is passed a configuration
    dictionary containing the expected column structure."""
    tasks = [
        (
            create_fuel_commodity_df,
            {
                "Columns": [
                    "Csets",
                    "Region",
                    "CommName",
                    "Unit",
                    "LimType",
                    "CTSLvl",
                    "Ctype",
                ]
            },
            "tra_fuel_commodity_definitions.csv",
        ),
        (
            create_fuel_process_df,
            {"Columns": ["Sets", "Region", "TechName", "Tact", "Tcap", "Tslvl"]},
            "tra_fuel_process_definitions.csv",
        ),
        (
            create_commodity_df,
            {"Columns": ["Csets", "Region", "CommName", "Unit", "LimType"]},
            "tra_commodity_definitions.csv",
        ),
        (
            create_process_df,
            {"Columns": ["Sets", "Region", "TechName", "Tact", "Tcap"]},
            "tra_process_definitions.csv",
        ),
        (
            create_fuel_process_parameters_df,
            {
                "Columns": [
                    "TechName",
                    "Region",
                    "Comm-In",
                    "Comm-Out",
                    "Share-I~UP",
                    "Share-I~UP~2025",
                    "Share-I~UP~2060",
                    "EFF",
                    "Life",
                    "FIXOM",
                    "VAROM",
                    "FLO_DELIV",
                ]
            },
            "tra_fuel_process_parameters.csv",
        ),
        (
            create_process_parameters_df,
            {
                "Columns": [
                    "TechName",
                    "Region",
                    "Comm-In",
                    "Comm-Out",
                    "EFF",
                    "LIFE",
                    "ACT_BND~2023",
                    "ACT_BND~0",
                    "CAP2ACT",
                    "AFA",
                    "INVCOST",
                    "FIXOM",
                    "PRC_resid~2023",
                    "PRC_resid~2045",
                    "PRC_resid~2050",
                    "Share",
                    "Share~0",
                    "CEFF",
                ]
            },
            "tra_process_parameters.csv",
        ),
        (
            creat_process_paramereters2_df,
            {"Columns": ["CommName", "Region", "2023"]},
            "tra_process_parameters2.csv",
        ),
        (
            emission_factors_df,
            {"Columns": ["CommName", "TRALPG", "TRAPET", "TRADSL", "TRAJET", "TRAFOL"]},
            "tra_emission_factors.csv",
        ),
    ]

    for builder, cfg, fname in tasks:
        logging.info("Building %s", fname)
        df = builder(cfg)
        outfile = OUTPUT_LOCATION / fname
        df.to_csv(outfile, index=False)
        logging.info("  → saved %s  (%d rows)", outfile.name, len(df))


if __name__ == "__main__":
    main()
