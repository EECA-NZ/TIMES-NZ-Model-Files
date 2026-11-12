import pandas as pd
from solve_times_nz.postprocessing import (
    _scenario_name,
    electricity_generation,
    energy_demand,
    energy_service_demand,
    snapshot_metadata,
)


def test_scenario_name_uses_versioned_case_directory(tmp_path):
    assert (
        _scenario_name(
            {"scenario_name": "steady-v3.0.9"},
            tmp_path / "manifest.json",
        )
        == "steady-v3.0.9"
    )


def _metadata(tmp_path):
    pd.DataFrame(
        {"Process": ["ELC_HYD"], "PlantName": ["Hydro"], "Technology": ["Hydro"]}
    ).to_csv(tmp_path / "electricity_generation_processes.csv", index=False)
    pd.DataFrame(
        {
            "Process": ["DMD"],
            "EndUse": ["Space heating"],
            "Sector": ["Residential"],
        }
    ).to_csv(tmp_path / "demand_processes.csv", index=False)
    pd.DataFrame(
        {"Commodity": ["ELC"], "Fuel": ["Electricity"], "CommodityGroup": ["Energy"]}
    ).to_csv(tmp_path / "energy_commodities.csv", index=False)
    pd.DataFrame({"commname": ["DMDOUT"], "csets": ["DEM"], "unit": ["PJ"]}).to_csv(
        tmp_path / "commodity_units.csv", index=False
    )


def test_core_outputs_apply_prep_metadata(tmp_path):
    _metadata(tmp_path)
    results = pd.DataFrame(
        {
            "Attribute": ["VAR_FOut", "VAR_FIn", "VAR_FOut"],
            "Process": ["ELC_HYD", "DMD", "DMD"],
            "Commodity": ["ELC", "ELC", "DMDOUT"],
            "PV": [3.0, 2.0, 1.0],
        }
    )

    generation = electricity_generation(results, tmp_path)
    demand = energy_demand(results, tmp_path)
    service = energy_service_demand(results, tmp_path)

    assert generation[["Variable", "Unit", "Value"]].to_dict("records") == [
        {"Variable": "Electricity generation", "Unit": "PJ", "Value": 3.0}
    ]
    assert demand[["Variable", "Unit", "Value"]].to_dict("records") == [
        {"Variable": "Energy demand", "Unit": "PJ", "Value": 2.0}
    ]
    assert service[["Variable", "Unit", "Value"]].to_dict("records") == [
        {"Variable": "Energy service demand", "Unit": "PJ", "Value": 1.0}
    ]


def test_snapshot_metadata_copies_csvs_once(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "labels.csv").write_text("Code\nA\n", encoding="utf-8")
    run_dir = tmp_path / "run"

    snapshot = snapshot_metadata(source, run_dir)
    (source / "labels.csv").write_text("Code\nB\n", encoding="utf-8")

    assert snapshot == run_dir / "postprocessed/metadata"
    assert (snapshot / "labels.csv").read_text(encoding="utf-8") == "Code\nA\n"
