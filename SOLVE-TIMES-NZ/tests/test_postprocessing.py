import json

import pandas as pd
import pytest

from solve_times_nz import postprocessing
from solve_times_nz.postprocessing import (
    _scenario_name,
    batteries,
    battery_flows,
    carbon_costs,
    demand_flex_flows,
    electricity_demand_by_timeslice,
    electricity_generation,
    energy_demand,
    energy_service_demand,
    energy_service_demand_by_timeslice,
    generation_by_timeslice,
    objective_function,
    snapshot_metadata,
    technology_capacity,
    transport_capacity,
    transport_energy_demand,
    transport_energy_service_demand,
)


def test_scenario_name_uses_versioned_case_directory(tmp_path):
    assert (
        _scenario_name(
            {"scenario_name": "steady-v3.0.9"},
            tmp_path / "manifest.json",
        )
        == "steady-v3.0.9"
    )


@pytest.mark.parametrize("failure", [None, "calculation", "write"])
def test_postprocess_marks_complete_only_after_all_writes(
    tmp_path, monkeypatch, failure
):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "scenario_name": "steady-v3.0.9",
                "postprocessing": {"status": "completed"},
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "results.vd").touch()
    (tmp_path / "postprocessed").mkdir()
    old_output = tmp_path / "postprocessed/energy_demand.parquet"
    old_output.write_bytes(b"old flat output")
    frame = pd.DataFrame({"Value": [1.0]})
    monkeypatch.setattr(postprocessing, "read_vd", lambda _: frame.copy())
    functions = (
        "electricity_generation",
        "energy_demand",
        "energy_service_demand",
        "electricity_demand_by_timeslice",
        "energy_service_demand_by_timeslice",
        "generation_by_timeslice",
        "transport_energy_demand",
        "transport_energy_service_demand",
        "transport_capacity",
        "technology_capacity",
        "objective_function",
        "primary_energy",
        "batteries",
        "battery_flows",
        "demand_flex_flows",
        "emissions",
        "carbon_costs",
    )
    for name in functions:
        monkeypatch.setattr(postprocessing, name, lambda *_: frame.copy())

    def fail(*_args, **_kwargs):
        raise ValueError("synthetic failure")

    if failure == "calculation":
        monkeypatch.setattr(postprocessing, "energy_demand", fail)
    if failure == "write":
        monkeypatch.setattr(pd.DataFrame, "to_parquet", fail)
    if failure:
        with pytest.raises(ValueError, match="synthetic failure"):
            postprocessing.postprocess_run(tmp_path, tmp_path)
        assert json.loads(manifest_path.read_text())["postprocessing"] == {
            "status": "running"
        }
        assert old_output.read_bytes() == b"old flat output"
    else:
        output = postprocessing.postprocess_run(tmp_path, tmp_path)
        status = json.loads(manifest_path.read_text())["postprocessing"]
        assert status["status"] == "completed"
        assert status["completed_at"]
        assert set(status["files"]) == {
            path.relative_to(output).as_posix() for path in output.rglob("*.parquet")
        }
        assert (output / "raw_results.parquet").is_file()
        assert (output / "labelled/energy_demand.parquet").is_file()
        assert not (output / "energy_demand.parquet").exists()


def _metadata(tmp_path):
    pd.DataFrame(
        {
            "Process": ["ELC_HYD"],
            "ProcessGroup": ["Electricity generation"],
            "PlantName": ["Hydro"],
            "TechnologyGroup": ["Hydro"],
            "Technology": ["Hydro"],
        }
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
    pd.DataFrame(
        {"Commodity": ["ELCCO2"], "CommodityGroup": ["Energy Emissions"]}
    ).to_csv(tmp_path / "emissions_commodities.csv", index=False)
    pd.DataFrame(
        {
            "Process": ["ELC_BAT_2H"],
            "TechnologyGroup": ["Utility-scale battery"],
            "Technology": ["Utility battery (2 hour)"],
        }
    ).to_csv(tmp_path / "battery_processes.csv", index=False)
    pd.DataFrame(
        {
            "Process": ["JD-WH_LOW-FLEX"],
            "TechnologyGroup": ["Demand flex"],
            "Technology": ["Ripple control"],
        }
    ).to_csv(tmp_path / "demand_flex_processes.csv", index=False)
    pd.DataFrame({"commname": ["DMDOUT"], "csets": ["DEM"], "unit": ["PJ"]}).to_csv(
        tmp_path / "commodity_units.csv", index=False
    )
    pd.DataFrame(
        {"TimeSlice": ["ANNUAL", "SUM-WK-D"], "YearFraction": [1.0, 0.5]}
    ).to_csv(tmp_path / "timeslices.csv", index=False)


def test_core_outputs_apply_prep_metadata(tmp_path):
    _metadata(tmp_path)
    results = pd.DataFrame(
        {
            "Attribute": [
                "VAR_FOut",
                "VAR_FIn",
                "VAR_FOut",
                "VAR_Cap",
                "VAR_FIn",
                "VAR_FOut",
            ],
            "Process": [
                "ELC_HYD",
                "ELC_HYD",
                "ELC_HYD",
                "ELC_HYD",
                "DMD",
                "DMD",
            ],
            "Commodity": ["ELC", "ELC", "ELCCO2", "-", "ELC", "DMDOUT"],
            "PV": [3.0, 2.0, 1.0, 4.0, 2.0, 1.0],
            "Scenario": ["steady-v3.0.9"] * 6,
            "Region": ["NI"] * 6,
            "Vintage": [2023] * 6,
            "TimeSlice": ["ANNUAL"] * 6,
            "Period": [2023] * 6,
        }
    )

    generation = electricity_generation(results, tmp_path)
    demand = energy_demand(results, tmp_path)
    service = energy_service_demand(results, tmp_path)

    assert generation[["Variable", "Unit", "Value"]].to_dict("records") == [
        {"Variable": "Electricity generation", "Unit": "PJ", "Value": 3.0},
        {"Variable": "Electricity fuel use", "Unit": "PJ", "Value": 2.0},
        {
            "Variable": "Electricity generation emissions",
            "Unit": "kt CO2e",
            "Value": 1.0,
        },
        {"Variable": "Electricity generation capacity", "Unit": "GW", "Value": 4.0},
    ]
    assert demand[["Variable", "Unit", "Value"]].to_dict("records") == [
        {"Variable": "Energy demand", "Unit": "PJ", "Value": 2.0}
    ]
    assert service[["Variable", "Unit", "Value"]].to_dict("records") == [
        {"Variable": "Energy service demand", "Unit": "PJ", "Value": 1.0}
    ]


def test_demand_timeslice_outputs_use_prep_year_fractions(tmp_path):
    _metadata(tmp_path)
    results = pd.DataFrame(
        {
            "Attribute": ["VAR_FIn", "VAR_FOut"] * 2,
            "Process": ["DMD"] * 4,
            "Commodity": ["ELC", "DMDOUT"] * 2,
            "PV": [1.0, 2.0] * 2,
            "Scenario": ["steady-v3.0.9"] * 4,
            "Region": ["NI"] * 4,
            "Vintage": [2023, 2023, 2024, 2024],
            "TimeSlice": ["SUM-WK-D"] * 4,
            "Period": [2023, 2023, 2024, 2024],
        }
    )

    electricity = electricity_demand_by_timeslice(results, tmp_path)
    service = energy_service_demand_by_timeslice(results, tmp_path)

    expected_gw = 277.777777778 / (0.5 * 24 * 365)
    assert electricity[["Variable", "Unit", "Value"]].to_dict("records") == [
        {
            "Variable": "Average output",
            "Unit": "GW",
            "Value": pytest.approx(expected_gw),
        }
    ]
    assert service[["Variable", "Unit", "Value"]].to_dict("records") == [
        {
            "Variable": "Average output",
            "Unit": "GW",
            "Value": pytest.approx(2 * expected_gw),
        }
    ]


def test_generation_by_timeslice_uses_prep_year_fractions(tmp_path):
    _metadata(tmp_path)
    results = pd.DataFrame(
        {
            "Attribute": ["VAR_FOut"] * 2,
            "Process": ["ELC_HYD"] * 2,
            "Commodity": ["ELC"] * 2,
            "PV": [1.0, 2.0],
            "Scenario": ["steady-v3.0.9"] * 2,
            "Region": ["NI"] * 2,
            "Vintage": [2023, 2024],
            "TimeSlice": ["SUM-WK-D"] * 2,
            "Period": [2023, 2024],
        }
    )

    result = generation_by_timeslice(results, tmp_path)

    expected_gw = 2 * 277.777777778 / (0.5 * 24 * 365)
    assert result[["Variable", "Unit", "Value"]].to_dict("records") == [
        {
            "Variable": "Average output",
            "Unit": "GW",
            "Value": pytest.approx(expected_gw),
        }
    ]


def test_transport_capacity_and_objective_outputs_use_prep_metadata(tmp_path):
    _metadata(tmp_path)
    pd.DataFrame(
        {
            "ProcessGroup": ["Demand", "Demand"],
            "Process": ["DMD", "T_C_CAR_LOW"],
            "CommodityOut": ["DMDOUT", "T_C_CAR"],
            "SectorGroup": ["Residential", "Transport"],
            "Sector": ["Residential", "Road Transport"],
            "EnduseGroup": ["Space heating", "Light vehicles"],
            "EndUse": ["Space heating", "Light vehicles"],
            "TechnologyGroup": ["Heating", "Battery Electric Vehicle"],
            "Technology": ["Electric resistance", "Battery Electric Vehicle"],
            "Utilisation": [None, "Low"],
        }
    ).to_csv(tmp_path / "demand_processes.csv", index=False)
    pd.DataFrame({"Commodity": ["T_C_CAR"]}).to_csv(
        tmp_path / "demand_commodities.csv", index=False
    )
    pd.DataFrame(
        {
            "commname": ["DMDOUT", "T_C_CAR"],
            "csets": ["DEM", "DEM"],
            "unit": ["PJ", "BVkm"],
        }
    ).to_csv(tmp_path / "commodity_units.csv", index=False)
    pd.DataFrame(
        {"techname": ["DMD"], "sets": ["DMD"], "tact": ["PJ"], "tcap": ["GW"]}
    ).to_csv(tmp_path / "process_units.csv", index=False)
    results = pd.DataFrame(
        {
            "Attribute": ["VAR_FIn", "VAR_FOut", "VAR_Cap", "VAR_Cap", "ObjZ"],
            "Process": ["T_C_CAR_LOW", "T_C_CAR_LOW", "T_C_CAR_LOW", "DMD", "-"],
            "Commodity": ["ELC", "T_C_CAR", "-", "-", "-"],
            "PV": [2.0, 3.0, 4.0, 5.0, 1_500.0],
            "Scenario": ["steady-v3.0.9"] * 5,
            "Region": ["NI"] * 5,
            "Vintage": [2024] * 5,
            "TimeSlice": ["SUM-WK-D"] * 5,
            "Period": [2024] * 5,
        }
    )

    results = pd.concat(
        [results, results.iloc[[1]].assign(Process="DMD", Commodity="DMDOUT", PV=6.0)],
        ignore_index=True,
    )

    service = energy_service_demand(results, tmp_path)
    assert service[["Commodity", "Unit", "Value"]].to_dict("records") == [
        {"Commodity": "DMDOUT", "Unit": "PJ", "Value": 6.0}
    ]
    transport_service = transport_energy_service_demand(results, tmp_path)
    assert transport_service[["Commodity", "Unit", "Value"]].to_dict("records") == [
        {"Commodity": "T_C_CAR", "Unit": "BVkm", "Value": 3.0}
    ]
    assert len(transport_energy_demand(results, tmp_path)) == 1
    assert transport_capacity(results, tmp_path)["Unit"].tolist() == ["000vehicles"]
    assert technology_capacity(results, tmp_path)["Unit"].tolist() == ["GW"]
    assert objective_function(results)["Value"].tolist() == [1.5]


def test_carbon_costs_preserve_measure_names_units_and_values():
    results = pd.DataFrame(
        {
            "Scenario": ["steady-v3.0.9"] * 3,
            "Period": [2030] * 3,
            "Region": ["NI"] * 3,
            "Commodity": ["TOTCO2"] * 3,
            "Attribute": ["VAR_FOut", "VAR_FOut", "Cost_Comx"],
            "PV": [60.0, 40.0, 5.0],
        }
    )

    result = carbon_costs(results)

    assert result[["Variable", "Unit", "Value"]].to_dict("records") == [
        {"Variable": "Total CO2 emissions", "Unit": "kt CO2", "Value": 100.0},
        {"Variable": "Carbon cost", "Unit": "Mio NZD", "Value": 5.0},
        {"Variable": "Carbon price", "Unit": "NZD/t CO2", "Value": 50.0},
    ]
    assert (
        result[["Scenario", "Period", "Region", "Commodity"]].to_dict("records")
        == [
            {
                "Scenario": "steady-v3.0.9",
                "Period": 2030,
                "Region": "NI",
                "Commodity": "TOTCO2",
            }
        ]
        * 3
    )


def test_snapshot_metadata_copies_csvs_once(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "labels.csv").write_text("Code\nA\n", encoding="utf-8")
    run_dir = tmp_path / "run"

    snapshot = snapshot_metadata(source, run_dir)
    (source / "labels.csv").write_text("Code\nB\n", encoding="utf-8")

    assert snapshot == run_dir / "postprocessed/metadata"
    assert (snapshot / "labels.csv").read_text(encoding="utf-8") == "Code\nA\n"


def test_batteries_publish_legacy_capacity_and_flow_outputs(tmp_path):
    _metadata(tmp_path)
    data = pd.DataFrame(
        {
            "Attribute": ["VAR_Cap", "VAR_FIn", "VAR_FOut"],
            "Process": ["ELC_BAT_2H"] * 3,
            "Commodity": ["-", "ELC", "ELC"],
            "PV": [1.2, 0.8, 0.6],
            "Scenario": ["steady-v3.0.9"] * 3,
            "Region": ["NI"] * 3,
            "Period": [2030] * 3,
            "TimeSlice": ["ANNUAL"] * 3,
            "Vintage": [2029] * 3,
        }
    )

    capacity = batteries(data, tmp_path)
    flows = battery_flows(data, tmp_path)

    assert capacity[["Technology", "Variable", "Unit", "Value"]].to_dict("records") == [
        {
            "Technology": "Utility battery (2 hour)",
            "Variable": "Capacity",
            "Unit": "GW",
            "Value": 1.2,
        },
    ]
    assert flows[["Technology", "Variable", "Unit", "Value"]].to_dict("records") == [
        {
            "Technology": "Utility battery (2 hour)",
            "Variable": "Battery charging",
            "Unit": "PJ",
            "Value": 0.8,
        },
        {
            "Technology": "Utility battery (2 hour)",
            "Variable": "Battery discharging",
            "Unit": "PJ",
            "Value": 0.6,
        },
    ]


def test_demand_flex_flows_publish_legacy_labels(tmp_path):
    _metadata(tmp_path)
    data = pd.DataFrame(
        {
            "Attribute": ["VAR_FIn", "VAR_FOut"],
            "Process": ["JD-WH_LOW-FLEX"] * 2,
            "Commodity": ["JD-HWATER_C-WH_LOW"] * 2,
            "PV": [0.8, 0.6],
            "Scenario": ["steady-v3.0.9"] * 2,
            "Region": ["NI"] * 2,
            "Period": [2030] * 2,
            "TimeSlice": ["SUM-WK-D"] * 2,
            "Vintage": [2029] * 2,
        }
    )

    result = demand_flex_flows(data, tmp_path)

    assert result[["Variable", "Technology", "Unit", "Value"]].to_dict("records") == [
        {
            "Variable": "Demand flex input",
            "Technology": "Ripple control",
            "Unit": "PJ",
            "Value": 0.8,
        },
        {
            "Variable": "Demand flex output",
            "Technology": "Ripple control",
            "Unit": "PJ",
            "Value": 0.6,
        },
    ]
