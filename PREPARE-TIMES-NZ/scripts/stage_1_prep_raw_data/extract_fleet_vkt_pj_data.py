"""
extract_fleet_vkt_pj_data.py

Generate a long-form Vehicle-Kilometres-Travelled (VKT) table for a given
year, pulling raw Excel inputs from *data_raw* and writing a CSV to
*data_intermediate*.
"""

# ────────────────────────────────────────────────────────────────
# Imports
# ────────────────────────────────────────────────────────────────

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd
from prepare_times_nz.filepaths import DATA_RAW, STAGE_1_DATA

# ──────────────────────────────────────────────────────────────── #
# Logging
# ──────────────────────────────────────────────────────────────── #
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ──────────────────────────────────────────────────────────────── #
# Constants - all paths use pathlib for cross-platform consistency
# ──────────────────────────────────────────────────────────────── #
INPUT_LOCATION_MOT = Path(DATA_RAW) / "external_data" / "mot"
INPUT_LOCATION_KIWIRAIL = Path(DATA_RAW) / "external_data" / "kiwirail"
INPUT_LOCATION_MBIE = Path(DATA_RAW) / "external_data" / "mbie"
INPUT_LOCATION_EEUD = Path(DATA_RAW) / "eeca_data" / "eeud"

OUTPUT_LOCATION = Path(STAGE_1_DATA) / "fleet_vkt_pj"
OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)

# ────────────────────────────────────────────────────────────────
# Constants
# ────────────────────────────────────────────────────────────────
ARTIC_CLASS_PERC = {
    "3.5-7.5": 0.0000,
    "7.5-10": 0.0100,
    "10-20": 0.2102,
    "20-25": 0.2317,
    "25-30": 0.3781,
    "> 30": 0.1700,
}

TRUCK_CLASS_PERC = {
    "3.5-7.5": 0.2038,
    "7.5-10": 0.0697,
    "10-20": 0.1278,
    "20-25": 0.1348,
    "25-30": 0.1908,
    "> 30": 0.2731,
}

ARTIC_ALLOCATION_MATRIX = np.array(
    [
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.1, 0.58, 0.21, 0.09, 0.02],
        [0.0, 0.0, 0.0, 0.29, 0.595, 0.115],
        [0.0, 0.0, 0.0, 0.01, 0.66, 0.33],
        [0.0, 0.0, 0.0, 0.0, 0.5, 0.5],
    ]
)

ARTIC_CLASSES = ["14-20 t", "20-28 t", "28-34 t", "34-40 t", "40-50 t", "50-60 t"]
ARTIC_KEYS = list(ARTIC_CLASS_PERC.keys())

# Mapping from (fueltype) to (fueltype, technology)
FUEL_TECHNOLOGY_REMAP = {
    "BEV": ("Electricity", "BEV"),
    "Diesel": ("Diesel", "ICE"),
    "Petrol": ("Petrol", "ICE"),
    "LPG": ("LPG", "ICE"),
}

VEHICLE_FUEL_TYPE_REMAP = {
    ("LPV Hybrid", "Petrol"): ("LPV", "Petrol", "ICE Hybrid"),
    ("LPV PHEV", "Petrol"): ("LPV", "Petrol", "PHEV"),
    ("LPV PHEV", "BEV"): ("LPV", "Electricity", "PHEV"),
    ("International Shipping", "Fuel Oil"): (
        "International Shipping",
        "Fuel Oil",
        "ICE",
    ),
    ("Domestic Shipping", "Fuel Oil"): ("Domestic Shipping", "Fuel Oil", "ICE"),
    ("International Aviation", "Av. Fuel/Kero"): (
        "International Aviation",
        "Av. Fuel/Kero",
        "Turbine Engine",
    ),
    ("Domestic Aviation", "Av. Fuel/Kero"): (
        "Domestic Aviation",
        "Av. Fuel/Kero",
        "Turbine Engine",
    ),
    ("Passenger Rail", "Diesel"): ("Passenger Rail", "Diesel", "ICE"),
    ("Rail Freight", "Diesel"): ("Rail Freight", "Diesel", "ICE"),
    ("Passenger Rail", "Electricity"): (
        "Passenger Rail",
        "Electricity",
        "Electric Motor",
    ),
    ("Rail Freight", "Electricity"): ("Rail Freight", "Electricity", "Electric Motor"),
}

TRUCK_NAMES = {
    "MedTr": "Light Truck",
    "HevTr": "Medium Truck",
    "VHevTr": "Heavy Truck",
}


# ────────────────────────────────────────────────────────────────
# Data-loading helpers
# ────────────────────────────────────────────────────────────────
def read_vehicle_counts_and_vkt(year: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """MOT workbook in *mot* folder."""
    counts = pd.read_csv(OUTPUT_LOCATION / "vehicle_counts_2023.csv")
    vkt_xls = INPUT_LOCATION_MOT / f"NZVehicleFleet_{year}.xlsx"
    vkt = pd.read_excel(vkt_xls, sheet_name="8.2a,b", header=1).iloc[
        :, :12
    ]  # first 12 cols only
    vkt["Year"] = pd.to_numeric(vkt["Year"], errors="coerce").astype("Int64")
    return counts, vkt[vkt["Year"] == year].round(6)


def read_energy_balance(sheet_name: str) -> pd.DataFrame:
    """MBIE energy balance in *mbie* folder."""
    xls = INPUT_LOCATION_MBIE / "energy-balance-tables.xlsx"
    return pd.read_excel(xls, sheet_name=sheet_name, header=[2, 3]).round(6)


def read_kiwirail_energy() -> pd.DataFrame:
    """Kiwirail fuel inputs in *kiwirail* folder (skips header rows)."""
    xls = INPUT_LOCATION_KIWIRAIL / "Kiwirail data check 2022-23 Input data.xlsx"
    return pd.read_excel(xls, skiprows=369).round(6)


def read_eeud_data() -> pd.DataFrame:
    """
    Reads EEUD data from the EECA directory and processes it into a DataFrame.
    """
    path = INPUT_LOCATION_EEUD / "EEUD_PJ_2023.xlsx"
    df = pd.read_excel(path, sheet_name="PJ")
    return df.rename(
        columns={
            "fuel": "fueltype",
            "technologyGroup": "vehicletype",
            "technology": "technology",
            "energyValue (PJ)": "pjvalue",
            "efficiency_vfm (PJ/mkm)": "efficiency_vfm_pj_mkm",
            "efficiency_vfm (L/100km)": "efficiency_vfm_l_100km",
            "efficiency_vfm (kWh/100km)": "efficiency_vfm_kwh_100km",
        }
    )


# ────────────────────────────────────────────────────────────────
# Business-rule helpers
# ────────────────────────────────────────────────────────────────


def enrich_with_eeud(df: pd.DataFrame, eeud: pd.DataFrame) -> pd.DataFrame:
    """
    Add PJ *and* efficiency metrics from EEUD to the long VKT table.
    """
    cols_to_bring = [
        "vehicletype",
        "fueltype",
        "technology",
        # "pjvalue",
        "efficiency_vfm_pj_mkm",
        "efficiency_vfm_l_100km",
        "efficiency_vfm_kwh_100km",
    ]

    out = df.merge(
        eeud[cols_to_bring],
        on=["vehicletype", "fueltype", "technology"],
        how="left",
        suffixes=("", "_eeud"),
    )

    return out


def get_bev_light_split(vehicle_counts):
    """
    Calculate the proportion of BEV (Battery Electric Vehicle) counts
    split between LPV and LCV types.
    """
    bev_light = vehicle_counts.query(
        'vehicletype in ["LPV", "LCV"] and custom_motive_group == "BEV"'
    )
    total = bev_light["vehicle_count"].sum()
    if total == 0:
        return 0, 0
    bev_lcv = bev_light.query('vehicletype == "LCV"')["vehicle_count"].sum()
    bev_lpv = bev_light.query('vehicletype == "LPV"')["vehicle_count"].sum()
    return round(bev_lcv / total, 4), round(bev_lpv / total, 4)


def get_truck_class_splits(travel_total, rigid_split, artic_pct, artic_class_split):
    """
    Calculate the split of truck travel between rigid and articulated classes.
    """
    total_artic = travel_total * artic_pct
    all_by_class = {k: travel_total * v for k, v in rigid_split.items()}
    artic_by_class = {
        k: total_artic * artic_class_split.get(k, 0) for k in artic_class_split
    }
    rigid_by_class = {
        k: all_by_class[k] - artic_by_class.get(k, 0) for k in all_by_class
    }
    return rigid_by_class, artic_by_class


def calculate_bev_diesel_vkt(vehicle_counts, class_info):
    """
    Calculate the VKT for BEV and Diesel vehicles in different truck classes.
    """
    results = {}
    for vehicletype, label, vkt_val in class_info:
        trucks = vehicle_counts.query(f'vehicletype == "{vehicletype}"')
        diesel_ev_total = trucks.query('custom_motive_group in ["Diesel_ICE", "BEV"]')[
            "vehicle_count"
        ].sum()

        if diesel_ev_total == 0:
            results[label] = (0, 0)
            continue

        bev_share = (
            trucks.query('custom_motive_group == "BEV"')["vehicle_count"].sum()
            / diesel_ev_total
        )
        diesel_share = (
            trucks.query('custom_motive_group == "Diesel_ICE"')["vehicle_count"].sum()
            / diesel_ev_total
        )

        results[label] = (
            round(vkt_val * bev_share, 6),
            round(vkt_val * diesel_share, 6),
        )
    return results


def get_petrol_splits(vehicle_counts, travel_total):
    """
    Calculate the petrol splits for LPV vehicles, including ICE, Hybrid, and PHEV.
    """
    lpv = vehicle_counts.query('vehicletype == "LPV"')
    counts = {
        "ICE": lpv.query('custom_motive_group == "Petrol_ICE"')["vehicle_count"].sum(),
        "Hybrid": lpv.query('custom_motive_group == "Petrol_Hybrid"')[
            "vehicle_count"
        ].sum(),
        "PHEV": lpv.query('custom_motive_group == "PHEV"')["vehicle_count"].sum() * 0.4,
    }
    total = sum(counts.values())

    if total == 0:
        return 0, 0, 0, 0

    pct = {k: v / total for k, v in counts.items()}
    phev_travel = travel_total * pct["PHEV"]
    phev_bev_part = phev_travel * 0.6 / 0.4

    return (
        travel_total * pct["ICE"],
        travel_total * pct["Hybrid"],
        phev_travel,
        phev_bev_part,
    )


def get_motorcycle_splits(vehicle_counts, travel_total):
    """Calculate the VKT split for motorcycles between BEV and petrol."""
    mcycle = vehicle_counts.query(
        'vehicletype == "Motorcycle" and custom_motive_group in ["Petrol_ICE", "BEV"]'
    )
    total = mcycle["vehicle_count"].sum()
    if total == 0:
        return 0, 0
    bev = mcycle.query('custom_motive_group == "BEV"')["vehicle_count"].sum() / total
    return travel_total * bev, travel_total * (1 - bev)


def estimate_lpg_vkt(vehicle_counts, petrol_row):
    """Estimate the VKT for LPG vehicles based on the petrol vehicle counts.
    This assumes LPG vehicles are a subset of petrol vehicles, using the
    ratio of petrol vehicle types to estimate LPG VKT."""
    vtypes = [
        vt for vt in petrol_row.index if vt in vehicle_counts["vehicletype"].unique()
    ]
    lpg_vkt = {}

    for vt in vtypes:
        petrol_ice = vehicle_counts.query(
            f'vehicletype == "{vt}" and custom_motive_group == "Petrol_ICE"'
        )["vehicle_count"].sum()
        petrol_hybrid = vehicle_counts.query(
            f'vehicletype == "{vt}" and custom_motive_group == "Petrol_Hybrid"'
        )["vehicle_count"].sum()
        lpg = vehicle_counts.query(
            f'vehicletype == "{vt}" and custom_motive_group == "LPG_ICE"'
        )["vehicle_count"].sum()

        total_petrol = petrol_ice + petrol_hybrid
        lpg_vkt[vt] = lpg * (petrol_row[vt] / total_petrol) if total_petrol > 0 else 0

    return lpg_vkt


def assemble_vkt_table(
    vkt_df,
    domestic_ship_jet_df,
    international_ship_jet_df,
    rail_df,
    vehicle_counts=None,
):
    """
    Assemble the VKT table by melting the VKT DataFrame and concatenating
    with domestic and international shipping, aviation, and rail data.

    vehicle_counts : pd.DataFrame, optional
        Currently unused, but included for compatibility with function calls.

    Returns:
    --------
    pd.DataFrame
        Long-form VKT and PJ table with fuel and technology types.
    """
    _ = vehicle_counts  # it's unused

    # Melt vkt_df to long-form
    vkt_long = (
        vkt_df.reset_index()
        .melt(id_vars="index", var_name="vehicletype", value_name="vktvalue")
        .rename(columns={"index": "fueltype"})
    )
    vkt_long["pjvalue"] = np.nan  # Add pjvalue column for consistency

    # Ensure all other DataFrames have the same columns
    for df in [domestic_ship_jet_df, international_ship_jet_df, rail_df]:
        if "vktvalue" not in df.columns:
            df["vktvalue"] = np.nan
        if "pjvalue" not in df.columns:
            df["pjvalue"] = np.nan

    # Concatenate all
    vkt_long = pd.concat(
        [vkt_long, domestic_ship_jet_df, international_ship_jet_df, rail_df],
        ignore_index=True,
    )

    vkt_long[["vehicletype", "fueltype", "technology"]] = vkt_long.apply(
        lambda row: pd.Series(
            VEHICLE_FUEL_TYPE_REMAP.get(
                (row["vehicletype"], row["fueltype"]),
                (row["vehicletype"],)
                + FUEL_TECHNOLOGY_REMAP.get(row["fueltype"], (row["fueltype"], None)),
            )
        ),
        axis=1,
    )

    vkt_long["vehicletype"] = vkt_long["vehicletype"].replace(TRUCK_NAMES)

    vkt_long = vkt_long[
        (vkt_long["vktvalue"].fillna(0) > 0) | (vkt_long["pjvalue"].fillna(0) > 0)
    ]

    # Sort
    vkt_long = vkt_long.sort_values(
        by=["vehicletype", "fueltype", "technology"], ignore_index=True
    )

    return vkt_long[["vehicletype", "fueltype", "technology", "vktvalue", "pjvalue"]]


# ────────────────────────────────────────────────────────────────
# Core driver
# ────────────────────────────────────────────────────────────────


def map_vehicle_counts_keys(vehicle_counts):
    """Map vehicle counts to a DataFrame with vehicle type, fuel type, and technology.
    It uses a mapping dictionary to remap certain vehicle types and fuel types."""

    def map_row(row):
        key = (row["vehicletype"], row["custom_motive_group"])
        if key in VEHICLE_FUEL_TYPE_REMAP:
            vt, ft, tech = VEHICLE_FUEL_TYPE_REMAP[key]
        else:
            vt = row["vehicletype"]
            ft, tech = FUEL_TECHNOLOGY_REMAP.get(
                row["custom_motive_group"], (row["custom_motive_group"], None)
            )
        return pd.Series([vt, ft, tech])

    vehicle_keys = vehicle_counts[
        ["vehicletype", "custom_motive_group"]
    ].drop_duplicates()
    vehicle_keys[["vehicletype", "fueltype", "technology"]] = vehicle_keys.apply(
        map_row, axis=1
    )
    return vehicle_keys[["vehicletype", "fueltype", "technology"]]


# pylint: disable=too-many-locals
# pylint: disable=too-many-function-args
def generate_vkt_long(year: int) -> pd.DataFrame:
    """Generate a long-form VKT table for the specified year.
    This function reads vehicle counts, VKT data, and energy balance data,
    processes the data to calculate various vehicle splits, and returns a
    long-form DataFrame with VKT and PJ values for different vehicle types
    and fuel types."""
    vehicle_counts, vkt = read_vehicle_counts_and_vkt(year)
    pj = read_energy_balance(str(year))
    pj_rail = read_kiwirail_energy()
    eeud = read_eeud_data()  # Step 1: Read EEUD data

    # ---------- BEV light-vehicle splits
    bev_lcv_pct, bev_lpv_pct = get_bev_light_split(vehicle_counts)
    light_bev_total = vkt.filter(like="Light pure electric travel", axis=1).iloc[0, 0]
    bev_lcv = light_bev_total * bev_lcv_pct
    bev_lpv = light_bev_total * bev_lpv_pct

    # ---------- Truck splits
    truck_total = vkt.filter(like="Truck diesel travel", axis=1).iloc[0, 0]
    rigid, artic = get_truck_class_splits(
        truck_total, TRUCK_CLASS_PERC, 0.41, ARTIC_CLASS_PERC
    )

    artic_vals = np.array([artic.get(k, 0) for k in ARTIC_KEYS])
    artic_df = pd.DataFrame(
        ARTIC_ALLOCATION_MATRIX * artic_vals[:, None],
        index=ARTIC_KEYS,
        columns=ARTIC_CLASSES,
    )

    medium = rigid["3.5-7.5"] + rigid["7.5-10"]
    heavy = (
        rigid["10-20"]
        + rigid["20-25"]
        + rigid["25-30"]
        + artic_df.iloc[:, :4].values.sum()
    )
    very_heavy = rigid["> 30"] + artic_df.iloc[:, 4:].values.sum()

    truck_classes = [
        ("MedTr", "Medium", medium),
        ("HevTr", "Heavy", heavy),
        ("VHevTr", "Very Heavy", very_heavy),
    ]
    bev_diesel_split = calculate_bev_diesel_vkt(vehicle_counts, truck_classes)

    # ---------- Petrol, motorcycles, other …
    petrol_travel = vkt.filter(like="Light passenger petrol travel", axis=1).iloc[0, 0]
    petrol_ice, petrol_hybrid, petrol_phev, phev_bev = get_petrol_splits(
        vehicle_counts, petrol_travel
    )

    motorcycle_travel = vkt.filter(like="Motorcycle travel", axis=1).iloc[0, 0]
    bev_motorcycle, petrol_motorcycle = get_motorcycle_splits(
        vehicle_counts, motorcycle_travel
    )

    petrol_lcv = vkt.filter(like="Light commercial petrol travel", axis=1).iloc[0, 0]
    petrol_med_truck = vkt.filter(like="Truck petrol travel", axis=1).iloc[0, 0]
    petrol_bus = vkt.filter(like="Bus petrol travel", axis=1).iloc[0, 0]
    diesel_lpv = vkt.filter(like="Light passenger diesel travel", axis=1).iloc[0, 0]
    diesel_lcv = vkt.filter(like="Light commercial diesel travel", axis=1).iloc[0, 0]
    diesel_bus = vkt.filter(like="Bus diesel travel", axis=1).iloc[0, 0]
    bev_bus = vkt.filter(like="Electric bus travel", axis=1).iloc[0, 0]

    vkt_data = {
        "Petrol": {
            "LPV": petrol_ice,
            "LPV Hybrid": petrol_hybrid,
            "LPV PHEV": petrol_phev,
            "LCV": petrol_lcv,
            "Bus": petrol_bus,
            "Motorcycle": petrol_motorcycle,
            "MedTr": petrol_med_truck,
        },
        "Diesel": {
            "LPV": diesel_lpv,
            "LCV": diesel_lcv,
            "Bus": diesel_bus,
            "MedTr": bev_diesel_split["Medium"][1],
            "HevTr": bev_diesel_split["Heavy"][1],
            "VHevTr": bev_diesel_split["Very Heavy"][1],
        },
        "BEV": {
            "LPV": bev_lpv,
            "LPV PHEV": phev_bev,
            "LCV": bev_lcv,
            "Bus": bev_bus,
            "Motorcycle": bev_motorcycle,
            "MedTr": bev_diesel_split["Medium"][0],
            "HevTr": bev_diesel_split["Heavy"][0],
            "VHevTr": bev_diesel_split["Very Heavy"][0],
        },
    }

    vkt_df = pd.DataFrame.from_dict(vkt_data, orient="index").round(6)
    vkt_df.loc["LPG"] = [
        estimate_lpg_vkt(vehicle_counts, vkt_df.loc["Petrol"]).get(col, 0)
        for col in vkt_df.columns
    ]

    # ---------- Ship / Jet PJ rows (MBIE sheet)
    label_col = (year, "Converted into Petajoules using Gross Calorific Values")
    label_col1 = (year, "Converted into Petajoules using Gross Calorific Values.1")
    # Helpful for configuring columns
    # print("pj[llabel_col] unique values:", pj[label_col].unique())
    # print("pj[llabel_col1] unique values:", pj[label_col1].unique())
    # Print the column headers (multi-index levels)
    # print("pj column headers (multi-index levels):")
    # print(pj.columns.tolist())

    domestic_transport_row = pj[pj[label_col] == "Transport"]
    domestic_ship_jet_df = pd.DataFrame(
        [
            {
                "fueltype": "Fuel Oil",
                "vehicletype": "Domestic Shipping",
                "pjvalue": domestic_transport_row[("Coal", "Oil.4")].values[0],
            },
            {
                "fueltype": "Av. Fuel/Kero",
                "vehicletype": "Domestic Aviation",
                "pjvalue": domestic_transport_row[("Coal", "Oil.5")].values[0],
            },
        ]
    )

    international_transport_row = pj[pj[label_col1] == "International Transport"]
    international_ship_jet_df = pd.DataFrame(
        [
            {
                "fueltype": "Fuel Oil",
                "vehicletype": "International Shipping",
                "pjvalue": international_transport_row[("Coal", "Oil.4")].values[0],
            },
            {
                "fueltype": "Av. Fuel/Kero",
                "vehicletype": "International Aviation",
                "pjvalue": international_transport_row[("Coal", "Oil.5")].values[0],
            },
        ]
    )

    # ---------- Rail PJ rows (Kiwirail sheet)
    rail_df = pj_rail[
        ["Fuel Type", "Transport", "End-use Energy (output energy)"]
    ].rename(
        columns={
            "Fuel Type": "fueltype",
            "Transport": "vehicletype",
            "End-use Energy (output energy)": "pjvalue",
        }
    )
    rail_df["pjvalue"] = pd.to_numeric(rail_df["pjvalue"], errors="coerce") / 1e3
    rail_df = rail_df[rail_df["vehicletype"].isin(["Passenger Rail", "Rail Freight"])]
    rail_df = rail_df[rail_df["fueltype"].isin(["Electricity", "Diesel"])]

    vkt_long = assemble_vkt_table(
        vkt_df, domestic_ship_jet_df, international_ship_jet_df, rail_df, vehicle_counts
    )

    # Step 2: Enrich vkt_long with EEUD data
    vkt_long = enrich_with_eeud(vkt_long, eeud)

    return vkt_long


# ────────────────────────────────────────────────────────────────
# Main Script
# ────────────────────────────────────────────────────────────────
def main() -> None:
    """Generate and save long-form VKT/PJ data for 2023."""
    logger.info("Starting VKT/PJ extraction for 2023…")
    OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)
    year = 2023
    vkt_long = generate_vkt_long(year)
    out_path = OUTPUT_LOCATION / f"vkt_by_vehicle_type_and_fuel_{year}.csv"
    vkt_long.to_csv(out_path, index=False)
    logger.info("VKT data written to %s", out_path)


if __name__ == "__main__":
    main()
