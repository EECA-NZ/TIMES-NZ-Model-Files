"""Unit tests for the stage-1 EEUD source merge."""

import importlib.util
from pathlib import Path

import pandas as pd


def load_extract_eeud():
    """Load the stage-1 EEUD script without running its entry point."""
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts/stage_1_prep_raw_data/extract_eeud.py"
    )
    spec = importlib.util.spec_from_file_location("extract_eeud", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_combined_eeud_uses_stationary_data_and_transport_only_from_full_source(
    monkeypatch,
):
    """The 2025 stationary extension must not invent 2025 transport data."""
    module = load_extract_eeud()
    stationary = pd.DataFrame(
        {
            "sector_group": ["Commercial", "Commercial"],
            "sector": ["Data Centers", "Data Centers"],
            "sector_anzsic": ["J592", "J592"],
            "fuel_group": ["Electricity", "Electricity"],
            "fuel": ["Electricity", "Electricity"],
            "technology_group": ["Electronics and Lights"] * 2,
            "technology": ["Electronics"] * 2,
            "end_use_group": ["Electronics and Lighting"] * 2,
            "end_use": ["Electronics and Other Electrical Uses"] * 2,
            "transport": ["Non-Transport"] * 2,
            "energy_value": [408.36, 739.264],
            "period_end_date": [pd.Timestamp("2023-12-31"), pd.Timestamp("2025-12-31")],
        }
    )
    full_eeud = pd.DataFrame(
        {
            "SectorGroup": ["Commercial", "Transport"],
            "Sector": ["Office Blocks", "Road Transport"],
            "SectorANZSIC": ["J", "Z002"],
            "FuelGroup": ["Electricity", "Fossil Fuels"],
            "Fuel": ["Electricity", "Petrol"],
            "TechnologyGroup": ["Electronics and Lights", "Mobile Motors"],
            "Technology": ["Electronics", "Internal Combustion Engine"],
            "EnduseGroup": ["Electronics and Lighting", "Mobile Motive Power"],
            "EndUse": ["Electronics and Other Electrical Uses", "Motive Power, Mobile"],
            "Transport": ["Non-Transport", "Light Vehicles"],
            "EnergyValue (Terrajoules)": [10.0, 20.0],
            "PeriodEndDate": [pd.Timestamp("2024-12-31"), pd.Timestamp("2024-12-31")],
        }
    )

    def read_eeud(_source_dir, filename, _sheet_name):
        return stationary if filename == module.STATIONARY_EEUD_FILENAME else full_eeud

    monkeypatch.setattr(module, "read_eeud", read_eeud)

    combined = module.read_combined_eeud()

    assert set(combined["SectorGroup"]) == {"Commercial", "Transport"}
    assert combined.loc[
        combined["SectorGroup"] == "Transport", "PeriodEndDate"
    ].dt.year.tolist() == [2024]
    assert combined.loc[
        combined["PeriodEndDate"].dt.year == 2025, "Transport"
    ].tolist() == ["Non-Transport"]


def test_clean_eeud_data_restores_established_fossil_fuel_group():
    """Keep the EEUD fuel-group label stable across source workbook vintages."""
    module = load_extract_eeud()
    raw = pd.DataFrame(
        {
            "Sector": ["Commercial"] * 3,
            "FuelGroup": ["Fossil Fuel", "Fossil Fuels", "Electricity"],
            "Fuel": ["Natural Gas", "Coal", "Electricity"],
            "Technology": ["Boiler Systems"] * 3,
            "EndUse": ["Space Heating"] * 3,
            "EnergyValue": [1.0, 2.0, 3.0],
            "PeriodEndDate": pd.to_datetime(["2025-12-31"] * 3),
        }
    )

    cleaned = module.clean_eeud_data(raw)

    assert cleaned["FuelGroup"].tolist() == [
        "Fossil Fuels",
        "Fossil Fuels",
        "Electricity",
    ]
