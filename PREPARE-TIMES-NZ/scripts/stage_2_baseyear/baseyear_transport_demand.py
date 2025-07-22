"""
baseyear_transport_demand.py

Builds the “base-year” transport-demand CSV by combining
    • VKT + PJ (generate_vkt_long)
    • vehicle-counts (generate_vehicle_counts)
    • lives, rail efficiency, vehicle costs

Output →  data_intermediate/stage_2_baseyear/transport_demand_2023.csv
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from prepare_times_nz.filepaths import DATA_RAW, STAGE_1_DATA, STAGE_2_DATA

# ──────────────────────────────────────────────────────────────── #
# Logging
# ──────────────────────────────────────────────────────────────── #
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ────────────────────────────────────────────────────────────────
# Constants-level paths
# ────────────────────────────────────────────────────────────────
INPUT_LOCATION_KIWIRAIL = Path(DATA_RAW) / "external_data" / "kiwirail"
INPUT_LOCATION_MBIE = Path(DATA_RAW) / "external_data" / "mbie"

INPUT_LOCATION_FLEET = Path(STAGE_1_DATA) / "fleet_vkt_pj"
INPUT_LOCATION_COST = Path(STAGE_1_DATA) / "vehicle_costs"

OUTPUT_LOCATION = Path(STAGE_2_DATA) / "transport"
OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)

# ────────────────────────────────────────────────────────────────
# Constants
# ────────────────────────────────────────────────────────────────
MOTIVE_GROUP_MAP = {
    "BEV":("Electricity", "BEV"),
    "Petrol_Hybrid": ("Petrol", "ICE Hybrid"),
    "Diesel_ICE": ("Diesel", "ICE"),
    "Petrol_ICE": ("Petrol", "ICE"),
    "LPG_ICE": ("LPG", "ICE"),
}

FUEL_SPLIT_MAP = {
    ("LPV", "PHEV"): [
        {"fueltype": "Petrol", "technology": "PHEV", "fraction": 0.4},
        {"fueltype": "Electricity", "technology": "PHEV", "fraction": 0.6},
    ]
}

REGIONAL_SPLIT = {
    "LPV": {"NI": 0.73, "SI": 0.27},
    "LCV": {"NI": 0.73, "SI": 0.27},
    "Motorcycle": {"NI": 0.73, "SI": 0.27},
    "Bus": {"NI": 0.73, "SI": 0.27},
    "Light Truck": {"NI": 0.73, "SI": 0.27},
    "Medium Truck": {"NI": 0.73, "SI": 0.27},
    "Heavy Truck": {"NI": 0.73, "SI": 0.27},
    ("Rail Freight", "Diesel"): {"NI": 0.74, "SI": 0.26},
    ("Rail Freight", "Electricity"): {"NI": 1.0, "SI": 0.0},
    ("Passenger Rail", "Diesel"): {"NI": 1.0, "SI": 0.0},
    ("Passenger Rail", "Electricity"): {"NI": 0.74, "SI": 0.26},
    "Domestic Aviation": {"NI": 0.58, "SI": 0.42},
    "International Aviation": {"NI": 0.80, "SI": 0.20},
    "Domestic Shipping": {"NI": 0.34, "SI": 0.66},
    "International Shipping": {"NI": 0.72, "SI": 0.28},
}

TRUCK_NAMES = {
    'MedTr': 'Light Truck',
    'HevTr': 'Medium Truck',
    'VHevTr': 'Heavy Truck',
}

FUEL_SHARE = {
    ("LPV", "Petrol", "PHEV"): {"fuelshare": 0.40},
    ("LPV", "Electricity", "PHEV"): {"fuelshare": 0.60},
    ("Heavy Truck", "Diesel", "Dual Fuel"): {"fuelshare": 0.70},
    ("Heavy Truck", "Hydrogen", "Dual Fuel"): {"fuelshare": 0.30},
    ("NI", "Passenger Rail", "Electricity"): {"fuelshare": 0.62},
    ("NI", "Passenger Rail", "Diesel"): {"fuelshare": 0.38},
    ("NI", "Rail Freight", "Diesel"): {"fuelshare": 0.98},
    ("NI", "Rail Freight", "Electricity"): {"fuelshare": 0.02},
}

FLEET_WORKBOOK_YEAR = 2023          # <-- workbook file to open
LIFE_ROW_YEAR       = 2022          # <-- rows we keep from sheet
CAP2ACT = 0.08      # Max annual travel distance (000 km)
ACT_BND_0 = -1      # Interpolation rule for ACT_BND

MJ_PER_LITRE = {
    "Petrol": 35.18,
    "Diesel": 38.49,
    "LPG": 26.3735798,
}

# ════════════════════════════════════════════════════════════════
# Data-reader helpers
# ════════════════════════════════════════════════════════════════

# def read_life_data(file_year: int) -> pd.DataFrame:
#     """Open NZVehicleFleet_<file_year>.xlsx and return sheet 7.1/7.2."""
#     path = MOT_DIR / f"NZVehicleFleet_{file_year}.xlsx"
#     return (
#         pd.read_excel(path, sheet_name="7.1,7.2", header=1)
#           .iloc[:, :7]
#           .rename(columns=str.strip)
#           .round(6)
#     )

def read_rail_data() -> pd.DataFrame:
    path = INPUT_LOCATION_KIWIRAIL / "Kiwirail data check 2022-23 Input data.xlsx"
    df = pd.read_excel(path, skiprows=369)
    return df.rename(columns=str.strip).round(6)

def read_energy_balance(sheet_name: str) -> pd.DataFrame:
    """MBIE energy balance in *mbie* folder."""
    xls = INPUT_LOCATION_MBIE / "energy-balance-tables.xlsx"
    return pd.read_excel(xls, sheet_name=sheet_name, header=[2, 3]).round(6)

def read_kiwirail_energy() -> pd.DataFrame:
    """Kiwirail fuel inputs in *kiwirail* folder (skips header rows)."""
    xls = INPUT_LOCATION_KIWIRAIL / "Kiwirail data check 2022-23 Input data.xlsx"
    return pd.read_excel(xls, skiprows=369).round(6)

# ════════════════════════════════════════════════════════════════
# Transform helpers
# ════════════════════════════════════════════════════════════════

# def process_life_data(row_year: int = LIFE_ROW_YEAR,
#                       file_year: int = FLEET_WORKBOOK_YEAR) -> pd.DataFrame:
#     """Filter the sheet to rows where 'Year out' == row_year."""
#     df = read_life_data(file_year)
#     cols_needed = ["Type", "Year out", "New Average Age"]
#     missing = [c for c in cols_needed if c not in df.columns]
#     if missing:
#         raise ValueError(f"Missing columns in life data: {missing}")

#     df = (
#         df[cols_needed]
#           .rename(columns={"Type": "vehicletype",
#                            "New Average Age": "life(years)"})
#           .query("`Year out` == @row_year")
#           .drop(columns="Year out")
#           .reset_index(drop=True)
#     )
  
#     df["vehicletype"] = df["vehicletype"].str.strip().replace({"Mcycl": "Motorcycle"})
#     df = df[~df["vehicletype"].isin(["Other", "Light"])]

#     # Expand generic "Truck" row into Light / Medium / Heavy
#     truck_rows = df[df["vehicletype"] == "Truck"]
#     if not truck_rows.empty:
#         expanded = truck_rows.loc[truck_rows.index.repeat(3)].copy()
#         expanded["vehicletype"] = ["Light Truck", "Medium Truck", "Heavy Truck"]
#         df = pd.concat([df[df["vehicletype"] != "Truck"], expanded], ignore_index=True)

#     return df


def vehicle_counts_expanded(vc: pd.DataFrame) -> pd.DataFrame:
    vc = vc.copy()
    vc["vehicletype"] = vc["vehicletype"].replace(TRUCK_NAMES)

    def expand_row(row):
        key = (row["vehicletype"], row["custom_motive_group"])
        motive = row["custom_motive_group"]

        if key in FUEL_SPLIT_MAP:
            return [
                {
                    "vehicletype": row["vehicletype"],
                    "fueltype": s["fueltype"],
                    "technology": s["technology"],
                    "vehicle_count": row["vehicle_count"] * s["fraction"],
                }
                for s in FUEL_SPLIT_MAP[key]
            ]
        if motive in MOTIVE_GROUP_MAP:
            fuel, tech = MOTIVE_GROUP_MAP[motive]
            return [
                {
                    "vehicletype": row["vehicletype"],
                    "fueltype": fuel,
                    "technology": tech,
                    "vehicle_count": row["vehicle_count"],
                }
            ]
        return [
            {
                "vehicletype": row["vehicletype"],
                "fueltype": None,
                "technology": None,
                "vehicle_count": row["vehicle_count"],
            }
        ]

    records = [rec for _, r in vc.iterrows() for rec in expand_row(r)]
    return pd.DataFrame(records)

def mbie_total_road_energy(year: int) -> pd.DataFrame:       
    pj = read_energy_balance(str(year))
    pj_rail = read_kiwirail_energy()

    # Define the label column to identify 'Transport' rows
    label_col = (year, "Converted into Petajoules using Gross Calorific Values")

    # Extract row for domestic transport
    transport_row = pj[pj[label_col] == "Transport"]

    # Build dataframe of initial road energy PJ values
    road_df = pd.DataFrame([
        {"fueltype": "LPG",         "pjvalue": transport_row[("Coal", "Oil.1")].values[0]},
        {"fueltype": "Petrol",      "pjvalue": transport_row[("Coal", "Oil.2")].values[0]},
        {"fueltype": "Diesel",      "pjvalue": transport_row[("Coal", "Oil.3")].values[0]},
        {"fueltype": "Electricity", "pjvalue": transport_row[("Electricity", "Electricity")].values[0]},
    ])

    # Read and process rail PJ rows
    rail_df = pj_rail[["Fuel Type", "Transport", "End-use Energy (output energy)"]].rename(
        columns={
            "Fuel Type": "fueltype",
            "Transport": "vehicletype",
            "End-use Energy (output energy)": "pjvalue"
        }
    )
    rail_df["pjvalue"] = pd.to_numeric(rail_df["pjvalue"], errors="coerce") / 1e3  # convert to PJ
    rail_df = rail_df[
        rail_df["vehicletype"].isin(["Passenger Rail", "Rail Freight"]) &
        rail_df["fueltype"].isin(["Electricity", "Diesel"])
    ]

    # Subtract rail PJ from diesel and electricity
    rail_pj_by_fuel = rail_df.groupby("fueltype")["pjvalue"].sum()

    def subtract_rail(fuel: str, df: pd.DataFrame) -> None:
        if fuel in rail_pj_by_fuel:
            idx = df["fueltype"] == fuel
            df.loc[idx, "pjvalue"] = (
                df.loc[idx, "pjvalue"] - rail_pj_by_fuel[fuel]
            ).clip(lower=0)

    subtract_rail("Diesel", road_df)
    subtract_rail("Electricity", road_df)

    return road_df.reset_index(drop=True)

def apply_productivity_penalty_on_afa(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """
    Applies a time-dependent productivity penalty to BEV heavy trucks by reducing their availability factor.
    Uses year-dependent values: 13% (2023), 7% (2030), 3% (2040) with linear interpolation.
    """
    # Define known penalty points
    penalty_schedule = {
        2023: 0.13,
        2030: 0.07,
        2040: 0.03,
    }

    # Interpolate for the given year
    years = sorted(penalty_schedule.keys())
    if year <= years[0]:
        penalty = penalty_schedule[years[0]]
    elif year >= years[-1]:
        penalty = penalty_schedule[years[-1]]
    else:
        for i in range(len(years) - 1):
            y0, y1 = years[i], years[i + 1]
            if y0 <= year <= y1:
                p0, p1 = penalty_schedule[y0], penalty_schedule[y1]
                # Linear interpolation
                penalty = p0 + (p1 - p0) * ((year - y0) / (y1 - y0))
                break

    logging.info(f"📉 Applying {penalty*100:.1f}% productivity penalty to BEV Heavy Trucks for year {year}")

    mask = (
        (df["vehicletype"] == "Heavy Truck") &
        (df["technology"] == "BEV") &
        (df["fueltype"] == "Electricity") &
        df["vktvalue"].notna()
    )

    df.loc[mask, "vktvalue"] *= (1 - penalty)

    return df

# ════════════════════════════════════════════════════════════════
# Enrichment helpers
# ════════════════════════════════════════════════════════════════
# def enrich_with_life(vkt_df, life_df):
#     out = vkt_df.merge(life_df, how="left", on="vehicletype")
#     out.loc[
#         out["vehicletype"].isin(["Domestic Aviation", "International Aviation", "Domestic Shipping", "International Shipping", "Passenger Rail", "Rail Freight"]),
#         "life(years)",
#     ] = 60
#     return out

# def enrich_with_efficiency(df, rail_df):

#     # Only keep necessary columns from rail_df
#     rail_df = rail_df[["vehicletype", "fueltype", "efficiency"]]

#     df = df.merge(
#         rail_df, on=["vehicletype", "fueltype"], how="left", suffixes=("", "_rail")
#     )
#     df["efficiency"] = df["efficiency"].fillna(df["efficiency_rail"])
#     df = df.drop(columns="efficiency_rail")
#     df.loc[df["vehicletype"].isin(["Domestic Aviation", "International Aviation", "Domestic Shipping", "International Shipping"]), "efficiency"] = 1.0
#     return df

def enrich_with_efficiency(df, rail_df):
    # Only keep necessary columns from rail_df
    rail_df = rail_df[["vehicletype", "fueltype", "efficiency"]].rename(columns={"efficiency": "efficiency_rail"})

    df = df.merge(rail_df, on=["vehicletype", "fueltype"], how="left")
    return df


def enrich_with_costs(df, cost_df):
    df = df.merge(
        cost_df[
            [
                "vehicletype",
                "fueltype",
                "technology",
                "cost_2023_nzd",
                "operation_cost_2023_nzd",
            ]
        ],
        on=["vehicletype", "fueltype", "technology"],
        how="left",
    ).fillna({"cost_2023_nzd": 0, "operation_cost_2023_nzd": 0})

    # explicit mapping for LPV PHEV (falls back to mean of existing rows)
    mask = (df["vehicletype"] == "LPV") & (df["technology"] == "PHEV")
    if mask.any():
        phev_costs = cost_df.loc[
            (cost_df["vehicletype"] == "LPV") & (cost_df["technology"] == "PHEV"),
            ["cost_2023_nzd", "operation_cost_2023_nzd"],
        ].mean()
        df.loc[mask, ["cost_2023_nzd", "operation_cost_2023_nzd"]] = phev_costs.values
    return df


# ════════════════════════════════════════════════════════════════
# Main pipeline
# ════════════════════════════════════════════════════════════════
def build_baseyear_table(year: int) -> pd.DataFrame:
    vkt_long = pd.read_csv(INPUT_LOCATION_FLEET / f"vkt_by_vehicle_type_and_fuel_{year}.csv")
    vkt_utils = pd.read_csv(INPUT_LOCATION_FLEET / f"vkt_in_utils_{year}.csv")
    vkt_shares = vkt_utils[["vehicletype", "tertile", "vktshare"]]
    life = vkt_utils[["vehicletype", "tertile", "scrap_p70"]].copy()
    life = life.rename(columns={"scrap_p70": "life(years)"})
    vehicle_counts = pd.read_csv(INPUT_LOCATION_FLEET / f"vehicle_counts_{year}.csv")
    #life_df = process_life_data()   # uses LIFE_ROW_YEAR & FLEET_WORKBOOK_YEAR
    counts_expanded = vehicle_counts_expanded(vehicle_counts)
    cost_df = pd.read_csv(INPUT_LOCATION_COST / f"vehicle_costs_by_type_fuel_{year}.csv")
    road_df = mbie_total_road_energy(year)

    # rail efficiency table
    rail_raw = read_rail_data()
    rail_eff = rail_raw.rename(
        columns={
            "Fuel Type": "fueltype",
            "Transport": "vehicletype",
            "Energy Efficiency": "efficiency",
        }
    )
    rail_eff["efficiency"] = pd.to_numeric(rail_eff["efficiency"], errors="coerce")
    rail_eff = round(rail_eff, 2)
    rail_eff = rail_eff[
        rail_eff["vehicletype"].isin(["Passenger Rail", "Rail Freight"])
        & rail_eff["fueltype"].isin(["Electricity", "Diesel"])
    ]

    # enrichment chain
    # df = enrich_with_life(vkt_long, life_df)
    df = enrich_with_costs(vkt_long, cost_df)
    df = enrich_with_efficiency(df, rail_eff)
    df = df.merge(counts_expanded, on=["vehicletype", "fueltype", "technology"], how="left")
    
    # Expand rows by region and apply split
    rows = []
    for _, row in df.iterrows():
        key = (row["vehicletype"], row["fueltype"])
        split = REGIONAL_SPLIT.get(key) or REGIONAL_SPLIT.get(row["vehicletype"])
        if split:
            for region, frac in split.items():
                new_row = row.copy()
                new_row["region"] = region
                new_row["vktvalue"] = row["vktvalue"] * frac if pd.notnull(row["vktvalue"]) else np.nan
                new_row["pjvalue"] = row["pjvalue"] * frac if pd.notnull(row["pjvalue"]) else np.nan
                new_row["vehicle_count"] = row["vehicle_count"] * frac if pd.notnull(row["vehicle_count"]) else np.nan
                rows.append(new_row)
    df = pd.DataFrame(rows)
    
    df = (df
       .merge(vkt_shares, on="vehicletype", how="left")   # adds tertile & vktshare
       .assign(vktvalue=lambda d: d["vktvalue"] * d["vktshare"])
       .drop(columns="vktshare")                      # keep if you still need it
    )

    df = df.merge(life, on=["vehicletype", "tertile"], how="left")
    
    df.loc[
    df["vehicletype"].isin([
        "Domestic Aviation", "International Aviation",
        "Domestic Shipping", "International Shipping",
        "Passenger Rail", "Rail Freight"
    ]),
    "life(years)"
    ] = 60

    df["pjvalue_original"] = df["pjvalue"]
    mask = df["pjvalue"].isna()
    df.loc[mask, "pjvalue"] = df.loc[mask, "vktvalue"] * df.loc[mask, "efficiency_vfm_pj_mkm"]

    # Step 1: Total PJ from model output
    pj_by_fuel_model = (
        df.groupby("fueltype", as_index=False)["pjvalue"]
        .sum()
        .rename(columns={"pjvalue": "pj_model"})
    )

    # Step 2: MBIE-derived total PJ
    pj_by_fuel_ref = road_df.rename(columns={"pjvalue": "pj_mbie"})  # from MBIE

    # Step 3: Compute scale factor
    pj_scaling = pj_by_fuel_model.merge(pj_by_fuel_ref, on="fueltype")
    pj_scaling["scale_factor"] = pj_scaling["pj_mbie"] / pj_scaling["pj_model"]

    # Step 4: Merge back to df and apply
    df = df.merge(pj_scaling[["fueltype", "scale_factor"]], on="fueltype", how="left")
    df["pjvalue"] = np.where(
        df["pjvalue_original"].isna(),
        df["pjvalue"] * df["scale_factor"],
        df["pjvalue_original"]  # leave raw values untouched
    )
    df = df.drop(columns="scale_factor")
    df = df.drop(columns="pjvalue_original")

    # Recalculate efficiency AFTER PJ scaling
    df["efficiency_calc"] = df["vktvalue"] / df["pjvalue"] / 1000

    # Use rail efficiency if available, otherwise fallback to calculated
    df["efficiency"] = df["efficiency_rail"].combine_first(df["efficiency_calc"])

    # Override motorcycle electricity efficiency manually
    motorcycle_mask = (df["vehicletype"] == "Motorcycle") & (df["fueltype"] == "Electricity")
    df.loc[motorcycle_mask, "efficiency"] = 2.82

    # Step: Add missing hydrogen truck rows if not already in the data
    required_rows = [
        {"vehicletype": "Heavy Truck", "fueltype": "Hydrogen", "technology": "H2R"},
        {"vehicletype": "Medium Truck", "fueltype": "Hydrogen", "technology": "H2R"},
    ]

    for row in required_rows:
        match = (
            (df["vehicletype"] == row["vehicletype"]) &
            (df["fueltype"] == row["fueltype"]) &
            (df["technology"] == row["technology"])
        )
        if not df[match].any().any():
            #logging.warning(f"⛔ Missing row: {row}. Appending with NaNs except efficiency.")
            new_row = {**row}
            for col in df.columns:
                if col not in new_row:
                    new_row[col] = np.nan
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    # Manually override hydrogen efficiencies
    df.loc[
        (df["vehicletype"] == "Heavy Truck") &
        (df["technology"] == "H2R") &
        (df["fueltype"] == "Hydrogen"),
        "efficiency"
    ] = 0.08

    df.loc[
        (df["vehicletype"] == "Medium Truck") &
        (df["technology"] == "H2R") &
        (df["fueltype"] == "Hydrogen"),
        "efficiency"
    ] = 0.11


    # Override for aviation/shipping
    df.loc[
        df["vehicletype"].isin([
            "Domestic Aviation", "International Aviation",
            "Domestic Shipping", "International Shipping"
        ]),
        "efficiency"
    ] = 1.0

    def to_l_per_100km(row):
        fuel = row["fueltype"]
        eff = row["efficiency_calc"]
        if pd.notnull(eff) and fuel in MJ_PER_LITRE:
            return 100 / (eff * MJ_PER_LITRE[fuel])
        return np.nan

    df["fuel_consumption"] = df.apply(to_l_per_100km, axis=1)


    # For electricity: MJ to kWh conversion factor is 3.6
    df["energy_consumption"] = np.where(
        (df["fueltype"] == "Electricity") & df["efficiency"].notna(),
        100 / (df["efficiency"] * 3.6),
        np.nan
    )

    MJ_PER_KG_HYDROGEN = 120

    df["hydrogen_consumption"] = np.where(
        (df["fueltype"] == "Hydrogen") & df["efficiency"].notna(),
        100 / (df["efficiency"] * MJ_PER_KG_HYDROGEN),
        np.nan
    )

    # Drop temp columns
    df = df.drop(columns=["efficiency_rail", "efficiency_calc"])

    df["Cap2Act"] = np.where(df["vehicle_count"] > 0, CAP2ACT, np.nan)
    df = apply_productivity_penalty_on_afa(df, year)
    df["ACT_BND_0"] = np.where(df["vehicle_count"] > 0, ACT_BND_0, np.nan)
    df["vktvalue"] = df["vktvalue"] / 1000    #converting to billion vkt
    df["vehicle_count"] = df["vehicle_count"] / 1000 # converting to 000vehicles
    df["vehicle_count"] = df["vehicle_count"] / 3
    df["annual_utilisation_rate"] = df["vktvalue"] / df["vehicle_count"] / df["Cap2Act"]
    df["cost_2023_nzd"] = df["cost_2023_nzd"] / 1000  # converting to 000NZD/vehicle
    df["operation_cost_2023_nzd"] = df["operation_cost_2023_nzd"] / 1000  # converting to 000NZD/km/vehicle

    # get FUEL_SHARE values
    def get_fuelshare(row):
        # Try (vehicletype, fueltype, technology)
        key1 = (row["vehicletype"], row["fueltype"], row["technology"])
        # Try (region, vehicletype, fueltype)
        key2 = (row["region"], row["vehicletype"], row["fueltype"])
        if key1 in FUEL_SHARE:
            return FUEL_SHARE[key1]["fuelshare"]
        elif key2 in FUEL_SHARE:
            return FUEL_SHARE[key2]["fuelshare"]
        else:
            return np.nan

    df["fuelshare"] = df.apply(get_fuelshare, axis=1)
    df = df.drop(columns=["efficiency_vfm_pj_mkm","efficiency_vfm_l_100km","efficiency_vfm_kwh_100km"])

    # Reshape to long format for selected variables
    value_vars = [
        "vktvalue", "pjvalue", "life(years)", "vehicle_count", "Cap2Act",
        "annual_utilisation_rate", "efficiency", "fuel_consumption", "energy_consumption", "hydrogen_consumption", "cost_2023_nzd", "operation_cost_2023_nzd", "ACT_BND_0", "fuelshare"
    ]
    unit_map = {
        "vktvalue": "billion km",
        "pjvalue": "PJ",
        "life(years)": "years",
        "vehicle_count": "000vehicles",
        "Cap2Act": "000km",
        "annual_utilisation_rate": "%",
        "efficiency": "billion km/PJ",
        "fuel_consumption": "L/100km",
        "energy_consumption": "kWh/100km",
        "hydrogen_consumption": "kg/100km",
        "cost_2023_nzd": "000NZD/vehicle",
        "operation_cost_2023_nzd": "000NZD/km/vehicle",
        "ACT_BND_0": "",
        "fuelshare": "%"
    }

    id_vars = [c for c in df.columns if c not in value_vars]
    df_long = df.melt(id_vars=id_vars, value_vars=value_vars,
                      var_name="variable", value_name="value")
    df_long["unit"] = df_long["variable"].map(unit_map)

    # Optionally, reorder columns
    cols = id_vars + ["variable", "value", "unit"]
    df_long = df_long[cols]

    return df_long

# ────────────────────────────────────────────────────────────────
# Main Script
# ────────────────────────────────────────────────────────────────
def main() -> None:
    """Generate base-year transport-demand CSV."""
    logger.info("Starting baseyear data extraction…")
    OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)
    year = 2023
    baseyear_df = build_baseyear_table(year)
    out_path = OUTPUT_LOCATION / f"transport_demand_{year}.csv"
    baseyear_df.to_csv(out_path, index=False)
    logger.info("baseyear data written to %s", out_path)

if __name__ == "__main__":
    main()