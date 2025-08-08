"""
Extract and tidy MBIE data sources for the TIMES-NZ preparation pipeline.

Here we find the MBIE excel files and create
"data_intermediate/stage_1_external_data/mbie/*". This will include any EDGS
assumptions we want to use and any official figures we want.
We also do some tidying/standardising here.
Potential to-do: something from the oil/gas forecasts, maybe balance tables,
primary production, that sort of thing.

Outputs are written to:

    data_intermediate/stage_1_external_data/mbie/*

Files produced
--------------
- mbie_ele_generation_gwh.csv
- mbie_ele_generation_pj.csv
- mbie_ele_only_generation.csv
- mbie_generation_capacity.csv
- gen_stack.csv
- mbie_gas_non_energy.csv
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
from prepare_times_nz.utilities.filepaths import DATA_RAW, STAGE_1_DATA

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------------
# Constants & I/O locations
# ---------------------------------------------------------------------------
INPUT_DIR = Path(DATA_RAW) / "external_data" / "mbie"
OUTPUT_DIR = Path(STAGE_1_DATA) / "mbie"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _read_edgs_sheet(sheet_name: str) -> pd.DataFrame:
    """Return a sheet from MBIE's EDGS assumptions workbook."""
    edgs_path = (
        INPUT_DIR / "electricity-demand-generation-scenarios-2024-assumptions.xlsx"
    )
    return pd.read_excel(edgs_path, sheet_name=sheet_name)


def _get_mbie_electricity(
    sheet_name: str,
    row_slice: slice,
    category_name: str,
    unit: str,
    variable_name: str,
) -> pd.DataFrame:
    """Generic loader for tables in 'electricity.xlsx'."""
    ele_path = INPUT_DIR / "electricity.xlsx"
    df = pd.read_excel(ele_path, sheet_name=sheet_name, skiprows=8)
    df = df.iloc[row_slice]
    df = df.drop("Annual % change", axis=1)
    # relabel the category year
    df = df.rename(columns={"Calendar year": category_name})
    # remove the footnote numbers from the categories
    df[category_name] = df[category_name].str.replace(r"\d+$", "", regex=True)
    # self-documenting table variables
    df["Unit"] = unit
    df["Variable"] = variable_name
    # pivot
    df = pd.melt(
        df, id_vars=["Fuel", "Unit", "Variable"], var_name="Year", value_name="Value"
    ).rename(columns={"Fuel": "FuelType"})
    return df


def _get_mbie_gen_ele_only() -> pd.DataFrame:
    """Electricity generation (no cogen) by fuel, GWh."""
    ele_path = INPUT_DIR / "electricity.xlsx"
    df = pd.read_excel(
        ele_path,
        sheet_name="6 - Fuel type (GWh)",
        usecols="B:K",
        skiprows=5,
        nrows=51,
    )
    df = (
        df.rename(columns={"Unnamed: 1": "Year"})
        .loc[lambda d: d["Year"].notna()]
        .drop(columns=["Unnamed: 2"])
    )
    df = df.rename(columns={"Oil1": "Oil", "Geo- thermal": "Geothermal"})
    df = df.melt(id_vars="Year", var_name="Fuel", value_name="Value")
    df["Unit"] = "GWh"
    df["Variable"] = "Electricity generation (no cogen)"
    df = df.rename(columns={"Fuel": "FuelType"})
    df["Year"] = df["Year"].astype(int)
    return df


def _get_official_electricity_capacity() -> pd.DataFrame:
    """Installed generation capacity (MW) by technology."""
    ele_path = INPUT_DIR / "electricity.xlsx"
    df = pd.read_excel(
        ele_path,
        sheet_name="7 - Plant type (MW)",
        usecols="B:P",
        skiprows=5,
        nrows=50,
    )
    df = (
        df.rename(columns={"Unnamed: 1": "Year"})
        .loc[lambda d: d["Year"].notna()]
        .drop(columns=["Sub-total", "Sub-total.1", "Unnamed: 15"])
        .rename(
            columns={
                "Gas3": "Gas Cogen",
                "Other4": "Other Cogen",
                "Other Thermal2": "Other electricity generation",
            }
        )
    )
    df = df.melt(id_vars="Year", var_name="Technology", value_name="Value")
    df["Value"] = df["Value"].fillna(0)
    df["Unit"] = "MW"
    df["Variable"] = "Electricity generation capacity at end year"
    df["Year"] = df["Year"].astype(int)
    return df


def _get_mbie_gas_pj(
    row_slice: slice,
    category_name: str,
    unit: str,
    variable_name: str,
) -> pd.DataFrame:
    """Pull a slice of the Annual_PJ sheet from gas.xlsx."""
    gas_path = INPUT_DIR / "gas.xlsx"
    df = pd.read_excel(gas_path, sheet_name="Annual_PJ", skiprows=9)
    df = df.iloc[row_slice]
    df.columns = [col.strip() if isinstance(col, str) else col for col in df.columns]
    # relabel the category year
    df = df.rename(columns={"Calendar year": category_name})
    # remove the footnote numbers from the categories
    df[category_name] = df[category_name].str.replace(r"\d+$", "", regex=True)
    # self-documenting table variables
    df["Unit"] = unit
    df["Variable"] = variable_name
    # pivot
    df = pd.melt(
        df,
        id_vars=[category_name, "Unit", "Variable"],
        var_name="Year",
        value_name="Value",
    )
    return df[df["Value"].notna()]


# ---------------------------------------------------------------------------
# Main script
# ---------------------------------------------------------------------------


def main() -> None:
    """Execute all MBIE extract tasks and write CSVs."""
    logger.info("Loading MBIE electricity generation tables …")
    mbie_gwh = _get_mbie_electricity(
        "2 - Annual GWh",
        row_slice=slice(2, 12),
        category_name="Fuel",
        unit="GWh",
        variable_name="Annual net electricity generation",
    )
    mbie_gwh.to_csv(OUTPUT_DIR / "mbie_ele_generation_gwh.csv", index=False)

    mbie_pj = _get_mbie_electricity(
        "4 - Annual PJ",
        row_slice=slice(2, 12),
        category_name="Fuel",
        unit="PJ",
        variable_name="Annual net electricity generation",
    )
    mbie_pj.to_csv(OUTPUT_DIR / "mbie_ele_generation_pj.csv", index=False)

    logger.info("Loading electricity (no cogen) …")
    _get_mbie_gen_ele_only().to_csv(
        OUTPUT_DIR / "mbie_ele_only_generation.csv", index=False
    )

    logger.info("Loading installed capacity …")
    _get_official_electricity_capacity().to_csv(
        OUTPUT_DIR / "mbie_generation_capacity.csv", index=False
    )

    logger.info("Loading EDGS assumptions …")
    _read_edgs_sheet("Generation Stack").to_csv(
        OUTPUT_DIR / "gen_stack.csv", index=False
    )

    logger.info("Loading gas (non-energy use) …")
    _get_mbie_gas_pj(
        row_slice=slice(60, 61),
        category_name="Balance category",
        unit="PJ",
        variable_name="Natural gas non-energy use",
    ).to_csv(OUTPUT_DIR / "mbie_gas_non_energy.csv", index=False)

    logger.info("MBIE extraction complete → %s", OUTPUT_DIR)


if __name__ == "__main__":
    main()
