"""
extract_vkt_tertile_shares.py

- Reads MOT VKT tertile mean data from Excel.
- Calculates empirical scrappage percentiles for each vehicle type and tertile.
- Computes VKT summary statistics (vehicle count, VKT value, share, average, etc.).
- Merges all indicators into a single table, rounds values, and saves to CSV.

Designed for integration into TIMES-NZ transport sector modeling workflows.
"""

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

OUTPUT_LOCATION = Path(STAGE_1_DATA) / "fleet_vkt_pj"
OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)

MOT_FILE: Path = INPUT_LOCATION_MOT / "vkt_tertile_mean.xlsx"

# ────────────────────────────────────────────────────────────────
# Constants
# ────────────────────────────────────────────────────────────────
VEHICLE_RENAME = {
    "Bus": "Bus",
    "Light commercial": "LCV",
    "Light passenger": "LPV",
    "Motorcycle": "Motorcycle",
    "Truck 3.5 - <10t": "Light Truck",
    "Truck 10t - <30t": "Medium Truck",
    "Truck 30t+": "Heavy Truck",
}

# ──────────────────────────────────────────────────────────────── #
# helpers
# ──────────────────────────────────────────────────────────────── #


def survival_percentile(g: pd.DataFrame, p: float, n_col: str = "n_fleet") -> float:
    """Calculate the age at which a given cumulative survival percentile
    is reached for a fleet.

    This function computes the age corresponding to a specified survival percentile `p`
    based on cumulative fleet reduction. It assumes that the initial
    count of fleet (`n_col`) at age 0 is the baseline for survival calculation.
    """
    g = g.sort_values("age").copy()
    n0 = g[n_col].iloc[0]
    if n0 == 0 or g[n_col].isna().all():
        return np.nan
    g["cum_prop"] = 1 - g[n_col] / n0
    return float(np.interp(p, g["cum_prop"], g["age"]))


def empirical_scrappage_percentiles(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies age-weighted split of n_fleet into tertiles
    and computes empirical scrappage percentiles.
    """
    out = []

    for _, block in df.groupby("vehicle_size_group"):  # FIXED: unpack groupby tuple
        max_age = block["age"].max()
        if max_age == 0 or block["n_fleet"].sum() == 0:
            continue

        base_share = (
            block.groupby("tertile")["n_fleet"].sum().pipe(lambda s: s / s.sum())
        )

        block = block.copy()
        rank = block["tertile"]
        age_factor = 1 - block["age"] / max_age
        age_factor = age_factor.clip(lower=0)

        weight = base_share[rank].to_numpy() * (age_factor**rank)
        weight /= block.groupby("age")["tertile"].transform(lambda _, w=weight: w.sum())

        block["n_fleet"] *= weight

        for (vt2, t), g in block.groupby(["vehicle_size_group", "tertile"]):
            out.append(
                {
                    "vehicletype": vt2,
                    "tertile": t,
                    "scrap_p50": survival_percentile(g, 0.50),
                    "scrap_p60": survival_percentile(g, 0.60),
                    "scrap_p70": survival_percentile(g, 0.70),
                    "scrap_p80": survival_percentile(g, 0.80),
                }
            )

    return pd.DataFrame(out)


def first_year_vkt(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return VKT value at first full year in fleet (age 1 preferred,
    fallback to age 2 if missing) for each (vehicle_size_group, tertile) pair.
    """
    df = df.copy()
    df["tertile"] = df["tertile"].astype(int)

    age_1 = df[df["age"] == 1]
    age_2 = df[df["age"] == 2]

    # Merge both, prioritizing age 1
    vkt_age = pd.concat([age_1, age_2])
    vkt_age = vkt_age.sort_values("age").drop_duplicates(  # age 1 before 2
        subset=["vehicle_size_group", "tertile"], keep="first"
    )

    return vkt_age[["vehicle_size_group", "tertile", "vkt per tert"]].rename(
        columns={"vehicle_size_group": "vehicletype", "vkt per tert": "vkt_age_1"}
    )


def vkt_summary(df_yr: pd.DataFrame) -> pd.DataFrame:
    """This function computes a weighted average of annual VKT using fleet size,
    aggregates total VKT and fleet counts by group, and derives summary statistics
    including average VKT, VKT share, and an AFA (Annual Fleet Activity) indicator.
    """
    # Compute weighted annual VKT average and aggregate VKT/fleet size
    df_yr = df_yr.copy()
    df_yr["vkt_weighted"] = df_yr["annual_vkt_avg"] * df_yr["n_fleet"]

    summary = df_yr.groupby(["vehicle_size_group", "tertile"], as_index=False).agg(
        {"n_fleet": "sum", "vkt per tert": "sum", "vkt_weighted": "sum"}
    )

    summary["annual_vkt_avg"] = summary["vkt_weighted"] / summary["n_fleet"]

    # Rename and compute additional indicators
    summary = summary.rename(
        columns={
            "vehicle_size_group": "vehicletype",
            "vkt per tert": "vktvalue",
            "n_fleet": "vehiclecount",
        }
    )

    summary["vktshare"] = summary.groupby("vehicletype")["vktvalue"].transform(
        lambda x: x / x.sum()
    )
    summary["tertile_AFA"] = summary["annual_vkt_avg"] / 80_000

    return summary


# ---------------------------------------------------------------------
# main
# ---------------------------------------------------------------------
def main() -> None:
    """Computes VKT summary statistics"""
    logger.info("Reading MOT VKT tertile mean data from Excel…")
    OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)
    year = 2023
    df = pd.read_excel(MOT_FILE)
    df = df[df["year"] == 2023].copy()
    if "tertile" not in df or not set(df["tertile"].unique()) <= {0, 1, 2}:
        raise ValueError("Need integer tertile 0/1/2 column in MOT sheet.")
    df["tertile"] = df["tertile"].astype(int)

    # ---- Scrappage estimates
    empirical_df = empirical_scrappage_percentiles(df)
    # empirical_df = fallback_scrappage_heavy_to_medium(empirical_df)

    # ---- VKT summary + first year VKT
    base = vkt_summary(df)
    vkt_first_year = first_year_vkt(df)

    # ---- Merge everything
    vkt_utils = (
        base.merge(empirical_df, on=["vehicletype", "tertile"], how="left")
        .merge(vkt_first_year, on=["vehicletype", "tertile"], how="left")
        .replace({"vehicletype": VEHICLE_RENAME})
        .sort_values(["vehicletype", "tertile"])
    )

    cols = [
        "vehicletype",
        "tertile",
        "vehiclecount",
        "vktvalue",
        "annual_vkt_avg",
        "vktshare",
        "tertile_AFA",
        "vkt_age_1",
        "scrap_p50",
        "scrap_p60",
        "scrap_p70",
        "scrap_p80",
    ]

    # Round selected columns
    for col in [
        "vktvalue",
        "annual_vkt_avg",
        "vktshare",
        "tertile_AFA",
        "vkt_age_1",
        "scrap_p50",
        "scrap_p60",
        "scrap_p70",
        "scrap_p80",
    ]:
        vkt_utils[col] = vkt_utils[col].round(2)

    # Print result
    # print(vkt_utils[cols].to_string(index=False, float_format="%.2f"))

    out_path = OUTPUT_LOCATION / f"vkt_in_utils_{year}.csv"
    vkt_utils[cols].to_csv(out_path, index=False)
    logger.info("VKT utils summary statistics written to %s", out_path)


if __name__ == "__main__":
    main()
