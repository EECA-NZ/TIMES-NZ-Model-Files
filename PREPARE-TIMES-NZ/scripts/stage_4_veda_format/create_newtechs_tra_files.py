#!/usr/bin/env python3
"""
Stage 4 – VEDA-format builders for the transport (TRA) sector new technologies.

• Builds commodity / process / parameter tables
• Writes them to   DATA_INTERMEDIATE/stage_4_veda_format/future_year_tra
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from prepare_times_nz.stage_4.baseyear.transport import (
    create_process_df,
    create_process_parameters_df,
)

# Third party imports
from prepare_times_nz.utilities.filepaths import (
    STAGE_3_DATA,
    STAGE_4_DATA,
)

# Constants for file paths

OUTPUT_LOCATION = Path(STAGE_4_DATA) / "subres_tra"
OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)

SCENARIO_LOCATION = Path(STAGE_3_DATA) / "transport"
FUTURE_COSTS_FILE: Path = (
    SCENARIO_LOCATION / "vehicle_costs_by_type_fuel_projected_2023.csv"
)

# Constants for calculations
START = 2025
INVCOST_0 = 5
SCENARIO = ["Traditional", "Transformation"]

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


# pylint: disable=too-many-branches
# pylint: disable=too-many-locals
# pylint: disable=too-many-statements
# pylint: disable=duplicate-code
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


def load_cost_tables(costs: pd.DataFrame) -> pd.DataFrame:
    """Prepare cost tables for parameter calculations."""
    id_cols = [
        c
        for c in ("vehicletype", "fueltype", "technology", "scenario")
        if c in costs.columns
    ]
    out = costs.copy()
    for c in id_cols:
        out[c] = out[c].astype(str).str.strip().str.lower()

    prefixes = ("cost_", "operation_cost_")
    value_cols = [c for c in out.columns if c.startswith(prefixes)]
    keep = list(dict.fromkeys(id_cols + value_cols))
    out = out[keep].copy()

    if all(k in out.columns for k in id_cols) and value_cols:
        # Use local function name to avoid name conflict
        def _first_nonnull(s: pd.Series):
            return s.dropna().iloc[0] if s.notna().any() else pd.NA

        out = out.groupby(id_cols, as_index=False).agg(
            {c: _first_nonnull for c in value_cols}
        )
    else:
        out = out.drop_duplicates(subset=id_cols, keep="first")

    return out


def first_nonnull(s: pd.Series) -> float:
    """Return first non-null value from a Series, or np.nan if none found."""
    return s.dropna().iloc[0] if s.notna().any() else np.nan


# -----------------------------------------------------------------------------
# BUILDERS
# -----------------------------------------------------------------------------


def create_newtech_process_df(cfg):
    """Creates a DataFrame defining new transport technologies."""
    # get TechName values from create_process_df
    df_base = create_process_df({"Columns": ["TechName"]}).copy()

    # normalize
    df_base["TechName"] = df_base["TechName"].str.replace(r"NEW", "ELC", regex=True)
    df_base["TechName"] = df_base["TechName"].str.replace(r"USD", "ELC", regex=True)

    # Drop patterns
    drop_patterns = r"BICEPET|BICELPG|CICELPG|LTICEPET"
    df_base = df_base[
        ~df_base["TechName"].str.contains(drop_patterns, case=False, na=False)
    ]

    # Exclude specific names
    exclude_names = {
        "T_F_DSHIPP",
        "T_F_ISHIPP",
        "T_O_FuelJet",
        "T_O_FuelJet_Int",
        "T_R_RailDSL",
        "T_R_RailELC",
        "T_P_RailDSL",
        "T_P_RailELC",
    }
    df_base = df_base[~df_base["TechName"].isin(exclude_names)]

    # Add new tech names
    add_technames = [
        "T_C_CHYBDSL",
        "T_P_CFCH2R",
        "T_C_CFCH2R",
        "T_P_CPHEVDSL",
        "T_C_CPHEVDSL",
        "T_F_LTFCH2R",
        "T_F_MTFCH2R",
        "T_F_HTFCH2R",
        "T_P_BFCH2R",
    ]
    add_technames = [
        f"{name}_{lvl}" for name in add_technames for lvl in ("LOW", "MED", "HIGH")
    ]

    # Filter out excluded patterns
    add_technames = [
        t
        for t in add_technames
        if not pd.Series([t]).str.contains(drop_patterns, case=False, na=False).iloc[0]
    ]

    # Combine and deduplicate
    tech_names = df_base["TechName"].tolist() + add_technames
    tech_names = list(dict.fromkeys(tech_names))
    tech_names = [t for t in tech_names if t not in exclude_names]

    df = pd.DataFrame(
        {
            "Sets": "DMD",
            "TechName": tech_names,
            "Tact": "BVkm",
            "Tcap": "000vehicles",
            "Vintage": "YES",
        }
    )

    return df[cfg["Columns"]]


def create_newtech_process_parameters_df(cfg):
    """Get newtech parameters from coded assumptions"""

    costs = pd.read_csv(FUTURE_COSTS_FILE)
    costs_wide = load_cost_tables(costs)
    cols = [
        "TechName",
        "Comm-In",
        "Comm-Out",
        "EFF",
        "LIFE",
        "CAP2ACT",
        "AFA",
        "INVCOST",
        "FIXOM",
        "Share",
    ]

    newtechs_process = create_process_parameters_df({"Columns": cols}).copy()

    # Normalize TechName
    newtechs_process["TechName"] = (
        newtechs_process["TechName"]
        .astype(str)
        .str.replace(r"NEW", "ELC", regex=False)
        .str.replace(r"USD", "ELC", regex=False)
        .str.strip()
    )

    # Drop patterns
    drop_patterns = r"BICEPET|BICELPG|CICELPG|LTICEPET"
    newtechs_process = newtechs_process[
        ~newtechs_process["TechName"].str.contains(drop_patterns, na=False)
    ]

    exclude_names = {
        "T_F_DSHIPP",
        "T_F_ISHIPP",
        "T_O_FuelJet",
        "T_O_FuelJet_Int",
        "T_R_RailDSL",
        "T_R_RailELC",
        "T_P_RailDSL",
        "T_P_RailELC",
    }

    # Mapping of new techs with their Comm-In / Comm-Out roots
    add_newtechnames = [
        {"TechName": "T_C_CHYBDSL", "Comm-In": "TRADSL", "Comm-Out": "T_C_Car"},
        {
            "TechName": "T_P_CFCH2R",
            "Comm-In": "TRAH2R",
            "Comm-Out": "T_P_Car",
            "EFF": 0.735294117647059,
        },
        {
            "TechName": "T_C_CFCH2R",
            "Comm-In": "TRAH2R",
            "Comm-Out": "T_C_Car",
            "EFF": 0.735294117647059,
        },
        {
            "TechName": "T_P_CPHEVDSL",
            "Comm-In": "TRADSL",
            "Comm-Out": "T_P_Car",
            "Share": 0.4,
        },
        {
            "TechName": "T_P_CPHEVDSL",
            "Comm-In": "TRAELC",
            "Comm-Out": "T_P_Car",
            "Share": 0.6,
        },
        {
            "TechName": "T_C_CPHEVDSL",
            "Comm-In": "TRADSL",
            "Comm-Out": "T_C_Car",
            "Share": 0.4,
        },
        {
            "TechName": "T_C_CPHEVDSL",
            "Comm-In": "TRAELC",
            "Comm-Out": "T_C_Car",
            "Share": 0.6,
        },
        {
            "TechName": "T_F_LTFCH2R",
            "Comm-In": "TRAH2R",
            "Comm-Out": "T_F_LTrk",
            "EFF": 0.128205128205128,
        },
        {
            "TechName": "T_F_MTFCH2R",
            "Comm-In": "TRAH2R",
            "Comm-Out": "T_F_MTrk",
            "EFF": 0.110000000000000,
        },
        {
            "TechName": "T_F_HTFCH2R",
            "Comm-In": "TRAH2R",
            "Comm-Out": "T_F_HTrk",
            "EFF": 0.080000000000000,
        },
        {
            "TechName": "T_P_BFCH2R",
            "Comm-In": "TRAH2R",
            "Comm-Out": "T_P_Bus",
            "EFF": 0.161290322580645,
        },
    ]

    levels = ["LOW", "MED", "HIGH"]

    # Build the rows to add (expanding levels on TechName only)
    add_rows = []
    for item in add_newtechnames:
        base_comm_in = item.get("Comm-In", pd.NA)
        base_comm_out = item.get("Comm-Out", pd.NA)
        base_eff = item.get("EFF", pd.NA)
        base_share = item.get("Share", pd.NA)

        for lvl in levels:
            add_rows.append(
                {
                    "TechName": f'{item["TechName"]}_{lvl}',
                    "Comm-In": base_comm_in,
                    "Comm-Out": base_comm_out,
                    "EFF": base_eff,
                    "Share": base_share,
                }
            )

    add_df = pd.DataFrame(add_rows)

    # Remove any names that already exist (after cleaning) or are in the exclusion list
    existing = set(newtechs_process["TechName"].unique())
    add_df = add_df[~add_df["TechName"].isin(existing)]
    add_df = add_df[~add_df["TechName"].isin(exclude_names)]

    # Ensure all required columns on add_df
    for c in cols:
        if c not in add_df.columns:
            add_df[c] = pd.NA
    add_df = add_df[cols]

    out = pd.concat(
        [newtechs_process[cols], add_df.dropna(axis=1, how="all")], ignore_index=True
    )
    out = out[~out["TechName"].isin(exclude_names)]

    # De-duplicate by TechName + Comm-In (treat NaN Comm-In as equal)
    _dupe_sentinel = "__NA__"
    out = (
        out.assign(**{"Comm-In": out["Comm-In"].fillna(_dupe_sentinel)})
        .drop_duplicates(subset=["TechName", "Comm-In"], keep="first")
        .assign(**{"Comm-In": lambda d: d["Comm-In"].replace(_dupe_sentinel, pd.NA)})
    )

    # Add empty columns from cfg if missing
    for col in cfg["Columns"]:
        if col not in out.columns:
            out[col] = np.nan

    out["INVCOST~0"] = INVCOST_0
    out["START"] = START
    # START for Comm-Out T_F_HTrk, T_F_MTrk, T_P_Mcy is 2024
    mask_2024 = out["Comm-Out"].isin(["T_F_HTrk", "T_F_MTrk", "T_P_Mcy"])
    out.loc[mask_2024, "START"] = 2024

    # extract Level from TechName on the fly (no persistent column needed)
    _level = out["TechName"].astype(str).str.extract(r"_(LOW|MED|HIGH)$", expand=False)

    # 1) fill by exact (Comm-In, Comm-Out, Level)
    fill_exact = out.groupby([out["Comm-In"], out["Comm-Out"], _level])[
        "AFA"
    ].transform(first_nonnull)
    out["AFA"] = out["AFA"].fillna(fill_exact)

    # --- NEW: for H2R rows still missing AFA, use AFA from TRADSL with same Comm-Out & Level ---
    # make level a temporary column so we can join on it
    out = out.assign(_level=_level)

    # build reference AFA from TRADSL rows
    ref = (
        out.loc[
            out["Comm-In"].astype(str).str.contains(r"^TRADSL$", na=False),
            ["Comm-Out", "_level", "AFA"],
        ]
        .dropna(subset=["AFA"])
        .drop_duplicates(subset=["Comm-Out", "_level"], keep="first")
        .rename(columns={"AFA": "AFA_ref"})
    )

    # left-join the reference onto all rows
    out = out.merge(ref, how="left", on=["Comm-Out", "_level"])

    # fill only H2R rows that are still missing
    mask_h2r_missing = out["AFA"].isna() & out["Comm-In"].astype(str).str.contains(
        "H2R", na=False
    )
    out.loc[mask_h2r_missing, "AFA"] = out.loc[mask_h2r_missing, "AFA_ref"]

    # clean up temp columns
    out = out.drop(columns=["AFA_ref", "_level"])

    # --- LIFE fill by (Comm-Out, Level) with robust keys and alignment ---

    # 0) normalize key
    out["Comm-Out"] = out["Comm-Out"].astype(str).str.strip()

    # 1) (re)compute level *now* and keep as a column
    out["_level"] = (
        out["TechName"]
        .astype(str)
        .str.strip()
        .str.upper()
        .str.extract(r"_(LOW|MED|HIGH)\s*$", expand=False)
    )

    # 2) transform using the column (not an earlier Series)
    fill_exact = out.groupby(["Comm-Out", "_level"], dropna=False)["LIFE"].transform(
        first_nonnull
    )
    out["LIFE"] = out["LIFE"].fillna(fill_exact)

    # 3) clean up
    out = out.drop(columns=["_level"])

    # find masks
    is_phev = out["TechName"].str.contains("PHEV", na=False)
    is_ice = out["Comm-In"].str.contains(r"TRA(?:DSL|PET)", na=False)
    is_elc = out["Comm-In"].str.contains("ELC", na=False)
    is_hybrid = out["TechName"].str.contains("HYB", na=False)

    # get seed values
    ice_eff = (
        out.loc[is_phev & is_ice, "EFF"].dropna().iloc[0]
        if (out.loc[is_phev & is_ice, "EFF"].notna().any())
        else np.nan
    )
    elc_eff = (
        out.loc[is_phev & is_elc, "EFF"].dropna().iloc[0]
        if (out.loc[is_phev & is_elc, "EFF"].notna().any())
        else np.nan
    )
    hybrid_eff = (
        out.loc[is_hybrid, "EFF"].dropna().iloc[0]
        if (out.loc[is_hybrid, "EFF"].notna().any())
        else np.nan
    )

    # patch uniformly
    if pd.notna(ice_eff):
        out.loc[is_phev & is_ice, "EFF"] = ice_eff
    if pd.notna(elc_eff):
        out.loc[is_phev & is_elc, "EFF"] = elc_eff
    if pd.notna(hybrid_eff):
        out.loc[is_hybrid, "EFF"] = hybrid_eff

    orig_n = len(out)
    out = out.loc[out.index.repeat(len(SCENARIO))].copy()
    out["SCENARIO"] = np.tile(SCENARIO, orig_n)

    # keep it in the final output
    if "SCENARIO" not in cfg["Columns"]:
        cfg["Columns"].append("SCENARIO")

    afa_2050 = {
        "T_F_HTICEDSL": 1.55,
        "T_F_HTBEVELC": 1.44,
        "T_F_HTFCH2R": 1.55,
    }

    afa_2050_num = dict(afa_2050)

    # 2) Map by base TechName (ignore _LOW/_MED/_HIGH suffix)
    _base = out["TechName"].astype(str).str.replace(r"_(LOW|MED|HIGH)$", "", regex=True)
    out["AFA~2050"] = _base.map(afa_2050_num)

    # 3) Ensure it’s in your output columns
    if "AFA~2050" not in cfg["Columns"]:
        cfg["Columns"].append("AFA~2050")

    # ---- Merge yeared costs (2030/2040/2050) by attributes + scenario ----
    # 2b) parse veh/fuel/tech for each row in `out` using your existing parser
    #     parse_attrs(tech, comm_out, comm_in) -> (veh, fuel, ttype)
    parsed = out.apply(
        lambda r: pd.Series(
            parse_attrs(str(r["TechName"]), str(r["Comm-Out"]), r["Comm-In"])
        ),
        axis=1,
    )
    parsed.columns = ["vehicletype", "fueltype", "technology"]

    # lower-case to match costs_wide
    for c in ("vehicletype", "fueltype", "technology"):
        parsed[c] = parsed[c].astype(str).str.strip().str.lower()

    # attach parsed keys + normalized scenario
    out = out.join(parsed)
    out["scenario"] = out["SCENARIO"].astype(str).str.strip().str.lower()

    # 0) avoid pre-existing year cols duplicates
    out = out.drop(
        columns=["INVCOST~2030", "INVCOST~2040", "INVCOST~2050"], errors="ignore"
    )

    # 1) split PHEV vs non-PHEV
    is_phev = out["TechName"].astype(str).str.contains("PHEV", case=False, na=False)

    # 2) build a fuel-agnostic cost view for PHEV: group by (vehicletype, technology, scenario)
    value_cols = [
        c for c in costs_wide.columns if c.startswith(("cost_", "operation_cost_"))
    ]
    costs_phev = (
        costs_wide.drop(columns=["fueltype"], errors="ignore")
        .groupby(["vehicletype", "technology", "scenario"], as_index=False)
        .agg({c: first_nonnull for c in value_cols})
    )

    # 3) merge: non-PHEV uses full key incl. fueltype; PHEV ignores fueltype
    merge_on_full = ["vehicletype", "fueltype", "technology", "scenario"]
    merge_on_phev = ["vehicletype", "technology", "scenario"]

    merged_non = out.loc[~is_phev].merge(costs_wide, how="left", on=merge_on_full)
    merged_phev = out.loc[is_phev].merge(costs_phev, how="left", on=merge_on_phev)
    merged = pd.concat([merged_non, merged_phev], ignore_index=True)

    # 4) rename year columns
    rename_map = {
        "cost_2030": "INVCOST~2030",
        "cost_2040": "INVCOST~2040",
        "cost_2050": "INVCOST~2050",
    }
    present = {k: v for k, v in rename_map.items() if k in merged.columns}
    merged = merged.rename(columns=present)

    # 5) scale ONLY the year columns; do NOT change existing INVCOST
    for col in present.values():
        merged[col] = pd.to_numeric(merged[col], errors="coerce") / 1000.0

    # 6) fill NaN INVCOST from a *scaled* cost_2023_nzd, then drop it
    if "cost_2023_nzd" in merged.columns:
        merged["INVCOST"] = pd.to_numeric(merged.get("INVCOST"), errors="coerce")
        c2023_scaled = pd.to_numeric(merged["cost_2023_nzd"], errors="coerce") / 1000.0
        merged["INVCOST"] = merged["INVCOST"].fillna(c2023_scaled)
        merged = merged.drop(columns=["cost_2023_nzd"])

    if "operation_cost_2023_nzd" in merged.columns:
        merged["FIXOM"] = pd.to_numeric(merged.get("FIXOM"), errors="coerce")
        c2023_scaled = (
            pd.to_numeric(merged["operation_cost_2023_nzd"], errors="coerce") / 1000.0
        )
        merged["FIXOM"] = merged["FIXOM"].fillna(c2023_scaled)
        merged = merged.drop(columns=["operation_cost_2023_nzd"])

    # 7) FINAL de-dup: keep the row that has any cost populated for each unique process row
    has_cost_cols = [
        c
        for c in ["INVCOST", "INVCOST~2030", "INVCOST~2040", "INVCOST~2050", "FIXOM"]
        if c in merged.columns
    ]
    merged["_has_cost"] = merged[has_cost_cols].notna().any(axis=1).astype(int)

    # remove any leftover helper column if it exists
    merged = merged.drop(columns="_has_cost", errors="ignore")

    # de-duplicate while preserving original order (keep first)
    dedup_keys = ["TechName", "Comm-In", "Comm-Out", "SCENARIO"]
    merged = merged.drop_duplicates(subset=dedup_keys, keep="first").reset_index(
        drop=True
    )

    # 8) keep columns in cfg
    for col in ["INVCOST", "FIXOM", *present.values()]:
        if col in merged.columns and col not in cfg["Columns"]:
            cfg["Columns"].append(col)

    merged["CAP2ACT"] = merged["CAP2ACT"].fillna(0.08)

    out = merged
    return out[cfg["Columns"]]


# -----------------------------------------------------------------------------
# MAIN – orchestrate every builder & write CSVs
# -----------------------------------------------------------------------------
def main() -> None:
    """Generates and exports TIMES-NZ transport sector newt etchnologies
    definition and parameter tables."""

    processes = create_newtech_process_df(
        {"Columns": ["Sets", "TechName", "Tact", "Tcap", "Vintage"]}
    )

    df = create_newtech_process_parameters_df(
        {
            "Columns": [
                "TechName",
                "Comm-In",
                "Comm-Out",
                "SCENARIO",
                "START",
                "EFF",
                "AFA",
                "AFA~2050",
                "LIFE",
                "INVCOST",
                "INVCOST~2030",
                "INVCOST~2040",
                "INVCOST~2050",
                "INVCOST~0",
                "FIXOM",
                "CAP2ACT",
                "Share",
            ]
        }
    )
    df_standard_cost_curve = df[df["SCENARIO"] == "Traditional"].drop(
        columns="SCENARIO"
    )
    df_advanced_cost_curve = df[df["SCENARIO"] == "Transformation"].drop(
        columns="SCENARIO"
    )

    # save

    processes.to_csv(OUTPUT_LOCATION / "future_transport_processes.csv", index=False)

    df_standard_cost_curve.to_csv(
        OUTPUT_LOCATION / "future_transport_details_standard_costcurve.csv", index=False
    )
    df_advanced_cost_curve.to_csv(
        OUTPUT_LOCATION / "future_transport_details_advanced_costcurve.csv", index=False
    )


if __name__ == "__main__":
    main()
