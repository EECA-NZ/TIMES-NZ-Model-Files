"""Read MBIE workbooks and write the stage-1 MBIE datasets."""

from pathlib import Path

import pandas as pd
from prepare_times_nz.stage_1.mbie import (
    extract_electricity_demand_totals,
    extract_unallocated_onsite_generation,
    tidy_annual_electricity,
    tidy_contingent_reserves,
    tidy_energy_balance,
    tidy_gas_balance_category,
    tidy_generation_by_fuel,
    tidy_generation_capacity,
    tidy_production_profile,
)
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.filepaths import DATA_RAW, STAGE_1_DATA
from prepare_times_nz.utilities.logger_setup import logger

INPUT_DIR = Path(DATA_RAW) / "external_data/mbie"
OUTPUT_DIR = Path(STAGE_1_DATA) / "mbie"


def save_mbie_data(df: pd.DataFrame, name: str) -> None:
    """Save one staged MBIE dataset using the standard data writer."""
    _save_data(df, name, label="Saving MBIE data", filepath=OUTPUT_DIR)


def read_reserves_profile(
    sheet: str, columns: str, skiprows: int, rows: int
) -> pd.DataFrame:
    """Read one fixed-layout production-profile table from MBIE's reserves workbook."""
    return pd.read_excel(
        INPUT_DIR / "petroleum-reserves-1-jan-2026.xlsx",
        sheet_name=sheet,
        usecols=columns,
        skiprows=skiprows,
        nrows=rows,
    )


def extract_energy_balance() -> None:
    """Extract the machine-readable Energy Balance table."""
    logger.info("Loading machine-readable Energy Balance data …")
    energy_balance = pd.read_excel(
        INPUT_DIR / "energy-balance-tables.xlsx", sheet_name="Data"
    )
    save_mbie_data(tidy_energy_balance(energy_balance), "energy_balance.csv")


def extract_electricity() -> None:
    """Extract annual electricity, generation, and capacity tables."""
    electricity_path = INPUT_DIR / "electricity.xlsx"
    logger.info("Loading annual electricity generation …")
    annual_gwh = pd.read_excel(
        electricity_path, sheet_name="2 - Annual GWh", skiprows=8
    )
    annual_gwh = tidy_annual_electricity(
        annual_gwh,
        row_slice=slice(2, 12),
        category_name="Fuel",
        unit="GWh",
        variable_name="Annual net electricity generation",
    )
    save_mbie_data(annual_gwh, "mbie_ele_generation_gwh.csv")

    annual_pj = pd.read_excel(electricity_path, sheet_name="4 - Annual PJ", skiprows=8)
    annual_pj = tidy_annual_electricity(
        annual_pj,
        row_slice=slice(2, 12),
        category_name="Fuel",
        unit="PJ",
        variable_name="Annual net electricity generation",
    )
    save_mbie_data(annual_pj, "mbie_ele_generation_pj.csv")

    annual_pj_raw = pd.read_excel(
        electricity_path, sheet_name="4 - Annual PJ", header=None
    )
    logger.info("Loading unallocated onsite generation …")
    save_mbie_data(
        extract_unallocated_onsite_generation(annual_pj_raw),
        "unallocated_onsite_generation.csv",
    )

    electricity_balance = pd.read_excel(
        electricity_path, sheet_name="5 - Electricity Balance", header=None
    )
    save_mbie_data(
        extract_electricity_demand_totals(electricity_balance),
        "electricity_demand_totals.csv",
    )

    logger.info("Loading electricity generation and capacity …")
    generation_by_fuel = tidy_generation_by_fuel(
        pd.read_excel(electricity_path, sheet_name="6 - Fuel type (GWh)", header=None)
    )
    save_mbie_data(generation_by_fuel, "mbie_ele_only_generation.csv")
    generation_capacity = tidy_generation_capacity(
        pd.read_excel(electricity_path, sheet_name="7 - Plant type (MW)", header=None)
    )
    save_mbie_data(generation_capacity, "mbie_generation_capacity.csv")


def extract_edgs() -> None:
    """Extract electricity demand and generation scenario assumptions."""
    logger.info("Loading EDGS assumptions …")
    save_mbie_data(
        pd.read_excel(
            INPUT_DIR / "electricity-demand-generation-scenarios-2024-assumptions.xlsx",
            sheet_name="Generation Stack",
        ),
        "gen_stack.csv",
    )


def extract_gas() -> None:
    """Extract natural-gas non-energy use."""
    logger.info("Loading gas non-energy use …")
    gas_balance = pd.read_excel(
        INPUT_DIR / "gas.xlsx", sheet_name="Annual_PJ", skiprows=9
    )
    gas_non_energy = tidy_gas_balance_category(
        gas_balance,
        category="Non-Energy Use",
        category_name="Balance category",
        unit="PJ",
        variable_name="Natural gas non-energy use",
    )
    save_mbie_data(gas_non_energy, "mbie_gas_non_energy.csv")


def extract_reserves() -> None:
    """Extract petroleum production profiles and contingent reserves."""
    logger.info("Loading petroleum reserves …")
    gas_profile = tidy_production_profile(
        read_reserves_profile("Gas Production Profile", "B:AK", skiprows=3, rows=19),
        "Natural gas forecasts",
    )
    save_mbie_data(gas_profile, "natural_gas_forecasts.csv")

    lpg_profile = tidy_production_profile(
        read_reserves_profile("LPG Production Profile", "B:M", skiprows=3, rows=5),
        "LPG forecasts",
    )
    save_mbie_data(lpg_profile, "lpg_forecasts.csv")

    oil_profile = tidy_production_profile(
        read_reserves_profile("Oil Production Profile", "B:AK", skiprows=3, rows=19),
        "Oil and condensate",
    )
    save_mbie_data(oil_profile, "oil_forecasts.csv")

    contingent_reserves = tidy_contingent_reserves(
        read_reserves_profile("2C Resources", "B:F", skiprows=4, rows=18)
    )
    save_mbie_data(contingent_reserves, "contingent_reserves.csv")


def main() -> None:
    """Extract and stage all required MBIE datasets."""
    extract_energy_balance()
    extract_electricity()
    extract_edgs()
    extract_gas()
    extract_reserves()


if __name__ == "__main__":
    main()
