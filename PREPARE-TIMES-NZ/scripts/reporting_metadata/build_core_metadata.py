"""Publish PREP-owned reporting labels used by solver post-processing."""

import shutil
import tomllib
from pathlib import Path

import pandas as pd
from prepare_times_nz.reporting_metadata.core import (
    build_declaration_units,
    build_distribution_processes,
    build_electricity_generation_processes,
    build_energy_commodities,
    build_timeslices,
    uppercase_codes,
)

ROOT = Path(__file__).resolve().parents[2]
INTERMEDIATE = ROOT / "data_intermediate"
ASSUMPTIONS = ROOT / "data_raw/coded_assumptions/reporting"
OUTPUT = INTERMEDIATE / "postprocessing_metadata"
DOCUMENTATION_OUTPUT = ROOT / "docs/source/developer_guide/prepare_times_nz/data"


def _toml_table(data: dict) -> pd.DataFrame:
    """Expand one-value TOML fields to the length of its declared rows."""
    length = max(
        len(value) if isinstance(value, list) else 1 for value in data.values()
    )
    rows = {}
    for key, value in data.items():
        if not isinstance(value, list):
            rows[key] = [value] * length
        elif len(value) == 1:
            rows[key] = value * length
        elif len(value) == length:
            rows[key] = value
        else:
            raise ValueError(
                f"TOML field {key} has {len(value)} rows, expected {length}"
            )
    return pd.DataFrame(rows)


def _declared_tables(tag: str) -> list[pd.DataFrame]:
    """Read configured FI declaration tables for one VEDA tag."""
    metadata = pd.read_csv(INTERMEDIATE / "stage_0_config/config_metadata.csv")
    addresses = metadata.loc[
        metadata["VedaTag"] == tag, ["TableName", "DataLocation"]
    ].drop_duplicates()
    tables = []
    for table_name, address in addresses.itertuples(index=False):
        path = ROOT / address
        if path.suffix == ".csv":
            tables.append(pd.read_csv(path))
        elif Path(address).suffix == ".toml":
            path = INTERMEDIATE / "stage_0_config" / address
            with path.open("rb") as source:
                data = tomllib.load(source)[table_name]["Data"]
            tables.append(_toml_table(data))
        else:
            raise ValueError(f"Unsupported declaration source: {address}")
    return tables


def main() -> None:
    """Write metadata whose source is PREP declarations or reporting assumptions."""
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (INTERMEDIATE / "stage_0_config/SysSettings.toml").open("rb") as source:
        time_slices = tomllib.load(source)["TimeSlices"]["Data"]
    uppercase_codes(
        build_timeslices(
            time_slices,
            pd.read_csv(
                INTERMEDIATE / "stage_2_baseyear_data/settings/load_curves/yrfr.csv"
            ),
        )
    ).to_csv(OUTPUT / "timeslices.csv", index=False)
    fuels = pd.read_csv(ASSUMPTIONS / "fuel_labels.csv")
    sectors = pd.read_csv(ASSUMPTIONS / "sector_labels.csv")
    uppercase_codes(build_energy_commodities(fuels, sectors)).to_csv(
        OUTPUT / "energy_commodities.csv", index=False
    )
    distribution_extra = pd.read_csv(ASSUMPTIONS / "distribution_processes.csv")
    uppercase_codes(
        build_distribution_processes(fuels, sectors, distribution_extra)
    ).to_csv(OUTPUT / "distribution_processes.csv", index=False)
    electricity = build_electricity_generation_processes(
        pd.read_csv(
            INTERMEDIATE
            / "stage_2_baseyear_data/electricity/base_year_electricity_supply.csv"
        ),
        pd.read_csv(INTERMEDIATE / "stage_3_scenario_data/electricity/genstack.csv"),
        pd.read_csv(
            INTERMEDIATE / "stage_3_scenario_data/electricity/offshore_wind.csv"
        ),
        pd.read_csv(ASSUMPTIONS / "electricity_technology_labels.csv"),
    )
    uppercase_codes(electricity).to_csv(
        OUTPUT / "electricity_generation_processes.csv", index=False
    )
    uppercase_codes(
        build_declaration_units(
            _declared_tables("~FI_Process"), ["techname", "sets", "tact", "tcap"]
        )
    ).to_csv(OUTPUT / "process_units.csv", index=False)
    uppercase_codes(
        build_declaration_units(
            _declared_tables("~FI_Comm"), ["commname", "csets", "unit"]
        )
    ).to_csv(OUTPUT / "commodity_units.csv", index=False)
    for source, target in [
        ("production_processes.csv", "primary_production_processes.csv"),
        ("battery_processes.csv", "battery_processes.csv"),
        ("closure_processes.csv", "technical_processes.csv"),
        ("dummy_processes.csv", "dummy_processes.csv"),
        ("emissions_commodities.csv", "emissions_commodities.csv"),
        ("currency_commodities.csv", "currency_commodities.csv"),
        ("demand_flex_processes.csv", "demand_flex_processes.csv"),
    ]:
        uppercase_codes(pd.read_csv(ASSUMPTIONS / source)).to_csv(
            OUTPUT / target, index=False
        )
    DOCUMENTATION_OUTPUT.mkdir(parents=True, exist_ok=True)
    for source in OUTPUT.glob("*.csv"):
        shutil.copy2(source, DOCUMENTATION_OUTPUT / source.name)


if __name__ == "__main__":
    main()
