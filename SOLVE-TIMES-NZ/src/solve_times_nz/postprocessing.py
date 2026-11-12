"""Turn one completed VEDA result file into release-ready parquet outputs."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pandas as pd


def read_vd(path: Path) -> pd.DataFrame:
    """Read a GDX2VEDA ``.vd`` file without relying on QA-side discovery."""
    dimensions_pattern = re.compile(r"\*\s*Dimensions-")
    columns = None
    skiprows = 0
    with path.open(encoding="utf-8") as source:
        for line in source:
            if dimensions_pattern.search(line):
                columns = line.split("- ", maxsplit=1)[1].strip().split(";")
            if line.startswith('"'):
                break
            skiprows += 1
    if columns is None:
        raise ValueError(f"{path} has no VEDA Dimensions header")
    return pd.read_csv(
        path, skiprows=skiprows, names=columns, header=None, low_memory=False
    )


def _metadata(metadata_dir: Path, name: str) -> pd.DataFrame:
    path = metadata_dir / name
    if not path.is_file():
        raise ValueError(f"Missing PREP reporting metadata: {path}")
    return pd.read_csv(path)


def snapshot_metadata(metadata_dir: Path, run_dir: Path) -> Path:
    """Copy the generated PREP CSV contract into one solver-result release."""
    files = sorted(metadata_dir.glob("*.csv"))
    if not files:
        raise ValueError(f"No PREP reporting CSVs found in {metadata_dir}")
    destination = run_dir / "postprocessed" / "metadata"
    if destination.exists():
        return destination
    destination.mkdir(parents=True)
    for path in files:
        shutil.copy2(path, destination / path.name)
    return destination


def _with_value(df: pd.DataFrame, variable: str, unit: str) -> pd.DataFrame:
    result = df.copy()
    result["Variable"] = variable
    result["Unit"] = unit
    return result.rename(columns={"PV": "Value"})


def _scenario_name(manifest: dict[str, object], manifest_path: Path) -> str:
    """Read the versioned scenario identity declared by the generated case."""
    scenario = manifest.get("scenario_name")
    if not isinstance(scenario, str) or not scenario:
        raise ValueError(f"{manifest_path} has no scenario_name")
    return scenario


def electricity_generation(results: pd.DataFrame, metadata_dir: Path) -> pd.DataFrame:
    """Publish generation, fuel-use, capacity, and emissions for generators."""
    processes = _metadata(metadata_dir, "electricity_generation_processes.csv")
    commodities = pd.concat(
        [
            _metadata(metadata_dir, "energy_commodities.csv"),
            _metadata(metadata_dir, "emissions_commodities.csv"),
        ],
        ignore_index=True,
    )
    attributes = pd.DataFrame(
        [
            ("VAR_Cap", None, "Electricity generation capacity", "GW"),
            ("VAR_FIn", "Energy", "Electricity fuel use", "PJ"),
            ("VAR_FOut", "Energy", "Electricity generation", "PJ"),
            (
                "VAR_FOut",
                "Energy Emissions",
                "Electricity generation emissions",
                "kt CO2e",
            ),
        ],
        columns=["Attribute", "CommodityGroup", "Variable", "Unit"],
    )
    result = results[results["Attribute"].isin(attributes["Attribute"])].merge(
        processes, on="Process", how="inner", validate="many_to_one"
    )
    result = result.merge(
        commodities, on="Commodity", how="left", validate="many_to_one"
    )
    result = result.merge(
        attributes,
        on=["Attribute", "CommodityGroup"],
        how="left",
        validate="many_to_one",
    )
    capacity = result["Attribute"] == "VAR_Cap"
    result.loc[capacity, ["Variable", "Unit"]] = [
        "Electricity generation capacity",
        "GW",
    ]
    result = result[result["Variable"].notna()].rename(columns={"PV": "Value"})
    return result[
        [
            "Scenario",
            "Attribute",
            "Variable",
            "ProcessGroup",
            "Process",
            "PlantName",
            "TechnologyGroup",
            "Technology",
            "CommodityGroup",
            "Commodity",
            "Fuel",
            "Region",
            "Vintage",
            "TimeSlice",
            "Period",
            "Value",
            "Unit",
        ]
    ]


def energy_demand(results: pd.DataFrame, metadata_dir: Path) -> pd.DataFrame:
    """Label demand-device fuel inputs, excluding feedstock as current QA does."""
    processes = _metadata(metadata_dir, "demand_processes.csv")
    commodities = _metadata(metadata_dir, "energy_commodities.csv")
    result = results[(results["Attribute"] == "VAR_FIn")].merge(
        processes, on="Process", how="inner", validate="many_to_one"
    )
    result = result.merge(
        commodities, on="Commodity", how="inner", validate="many_to_one"
    )
    result = result[result["EndUse"] != "Feedstock"]
    return _with_value(result, "Energy demand", "PJ")


def energy_service_demand(results: pd.DataFrame, metadata_dir: Path) -> pd.DataFrame:
    """Label demand-device energy-service outputs using declared commodity units."""
    processes = _metadata(metadata_dir, "demand_processes.csv")
    units = _metadata(metadata_dir, "commodity_units.csv")
    units = units[units["csets"] == "DEM"].rename(
        columns={"commname": "Commodity", "unit": "Unit"}
    )[["Commodity", "Unit"]]
    result = results[(results["Attribute"] == "VAR_FOut")].merge(
        processes, on="Process", how="inner", validate="many_to_one"
    )
    result = result.merge(units, on="Commodity", how="inner", validate="many_to_one")
    result["Variable"] = "Energy service demand"
    return result.rename(columns={"PV": "Value"})


def _timeslice_average(data: pd.DataFrame, metadata_dir: Path) -> pd.DataFrame:
    """Convert PJ per timeslice to average GW using PREP year fractions."""
    timeslices = _metadata(metadata_dir, "timeslices.csv")[
        ["TimeSlice", "YearFraction"]
    ]
    result = data[data["Unit"] == "PJ"].merge(
        timeslices, on="TimeSlice", how="left", validate="many_to_one"
    )
    if result["YearFraction"].isna().any():
        missing = result.loc[result["YearFraction"].isna(), "TimeSlice"].unique()
        raise ValueError(f"Missing year fractions for timeslices: {', '.join(missing)}")
    result["Value"] = (
        result["Value"] * 277.777777778 / (result["YearFraction"] * 24 * 365)
    )
    result["Variable"] = "Average output"
    result["Unit"] = "GW"
    return result.drop(columns="YearFraction")


def electricity_demand_by_timeslice(
    results: pd.DataFrame, metadata_dir: Path
) -> pd.DataFrame:
    """Publish electricity demand as average GW for each non-base-year slice."""
    demand = energy_demand(results, metadata_dir)
    demand = demand[demand["Fuel"] == "Electricity"]
    if (demand["TimeSlice"] == "ANNUAL").any():
        raise ValueError(
            "Electricity demand processes must not use the ANNUAL timeslice"
        )
    result = _timeslice_average(demand, metadata_dir)
    base_year = pd.to_numeric(results["Period"], errors="coerce").min()
    return result[pd.to_numeric(result["Period"], errors="coerce") != base_year]


def energy_service_demand_by_timeslice(
    results: pd.DataFrame, metadata_dir: Path
) -> pd.DataFrame:
    """Publish PJ energy-service demand as average GW for each timeslice."""
    result = _timeslice_average(
        energy_service_demand(results, metadata_dir), metadata_dir
    )
    base_year = pd.to_numeric(results["Period"], errors="coerce").min()
    return result[pd.to_numeric(result["Period"], errors="coerce") != base_year]


def generation_by_timeslice(results: pd.DataFrame, metadata_dir: Path) -> pd.DataFrame:
    """Publish electricity generation as average GW for each timeslice."""
    result = electricity_generation(results, metadata_dir)
    result = _timeslice_average(
        result[result["Variable"] == "Electricity generation"], metadata_dir
    )
    base_year = pd.to_numeric(results["Period"], errors="coerce").min()
    result = result[pd.to_numeric(result["Period"], errors="coerce") != base_year]
    return result[
        [
            "Scenario",
            "Attribute",
            "Process",
            "PlantName",
            "TechnologyGroup",
            "Technology",
            "Region",
            "Vintage",
            "TimeSlice",
            "Period",
            "Variable",
            "Value",
            "Unit",
        ]
    ]


def _transport_processes(metadata_dir: Path) -> pd.DataFrame:
    """Return the PREP-labelled road-transport demand devices."""
    processes = _metadata(metadata_dir, "demand_processes.csv")
    return processes[
        (processes["SectorGroup"] == "Transport")
        & (processes["Sector"] == "Road Transport")
    ]


def transport_energy_demand(results: pd.DataFrame, metadata_dir: Path) -> pd.DataFrame:
    """Publish road-transport fuel use in the legacy transport-demand shape."""
    processes = _transport_processes(metadata_dir)
    fuels = _metadata(metadata_dir, "energy_commodities.csv")
    result = results[results["Attribute"] == "VAR_FIn"].merge(
        processes, on="Process", how="inner", validate="many_to_one"
    )
    result = result.merge(fuels, on="Commodity", how="inner", validate="many_to_one")
    result["Variable"] = "Transport Energy Demand"
    result["Unit"] = "PJ"
    result = result.rename(columns={"PV": "Value"})
    return result[
        [
            "Scenario",
            "Attribute",
            "Variable",
            "Sector",
            "ProcessGroup",
            "Process",
            "Utilisation",
            "CommodityGroup",
            "Commodity",
            "Fuel",
            "Period",
            "Region",
            "Vintage",
            "TimeSlice",
            "EnduseGroup",
            "EndUse",
            "TechnologyGroup",
            "Technology",
            "Unit",
            "Value",
        ]
    ]


def transport_energy_service_demand(
    results: pd.DataFrame, metadata_dir: Path
) -> pd.DataFrame:
    """Publish road-transport energy-service output in the legacy shape."""
    processes = _transport_processes(metadata_dir)
    demand_commodities = _metadata(metadata_dir, "demand_commodities.csv")
    result = results[results["Attribute"] == "VAR_FOut"].merge(
        processes, on="Process", how="inner", validate="many_to_one"
    )
    result = result.merge(
        demand_commodities[["Commodity"]],
        on="Commodity",
        how="inner",
        validate="many_to_one",
    )
    result["Variable"] = "Transport Energy Service Demand"
    result["Unit"] = "BVkm"
    result = result.rename(columns={"PV": "Value"})
    return result[
        [
            "Scenario",
            "Attribute",
            "Variable",
            "Sector",
            "ProcessGroup",
            "Process",
            "Utilisation",
            "Commodity",
            "Period",
            "Region",
            "Vintage",
            "TimeSlice",
            "EnduseGroup",
            "EndUse",
            "TechnologyGroup",
            "Technology",
            "Unit",
            "Value",
        ]
    ]


def transport_capacity(results: pd.DataFrame, metadata_dir: Path) -> pd.DataFrame:
    """Publish road-transport capacity in the legacy transport-capacity shape."""
    processes = _transport_processes(metadata_dir)
    result = results[results["Attribute"] == "VAR_Cap"].merge(
        processes, on="Process", how="inner", validate="many_to_one"
    )
    result["Variable"] = "Transport Capacity"
    result["Unit"] = "000vehicles"
    result = result.rename(columns={"PV": "Value"})
    return result[
        [
            "Scenario",
            "Attribute",
            "Variable",
            "Sector",
            "ProcessGroup",
            "Process",
            "Utilisation",
            "Period",
            "Region",
            "Vintage",
            "TimeSlice",
            "EnduseGroup",
            "EndUse",
            "TechnologyGroup",
            "Technology",
            "Unit",
            "Value",
        ]
    ]


def technology_capacity(results: pd.DataFrame, metadata_dir: Path) -> pd.DataFrame:
    """Publish non-transport demand-device capacity using declared capacity units."""
    processes = _metadata(metadata_dir, "demand_processes.csv")
    processes = processes[processes["SectorGroup"] != "Transport"]
    units = _metadata(metadata_dir, "process_units.csv")
    units = units[units["sets"] == "DMD"].rename(
        columns={"techname": "Process", "tcap": "Unit"}
    )[["Process", "Unit"]]
    units = units[units["Process"].isin(processes["Process"])]
    result = results[results["Attribute"] == "VAR_Cap"].merge(
        processes, on="Process", how="inner", validate="many_to_one"
    )
    result = result.merge(units, on="Process", how="inner", validate="many_to_one")
    result = result[result["Unit"] != "PJa"]
    result["Variable"] = "Technology Capacity"
    result = result.rename(columns={"PV": "Value"})
    return result[
        [
            "Scenario",
            "Attribute",
            "Variable",
            "ProcessGroup",
            "Process",
            "CommodityOut",
            "Period",
            "Region",
            "Vintage",
            "TimeSlice",
            "SectorGroup",
            "Sector",
            "EnduseGroup",
            "EndUse",
            "TechnologyGroup",
            "Technology",
            "Unit",
            "Value",
        ]
    ]


def objective_function(results: pd.DataFrame) -> pd.DataFrame:
    """Publish the single model objective in the legacy NZDb unit."""
    result = results[results["Attribute"] == "ObjZ"].copy()
    if len(result) != 1:
        raise ValueError(f"Expected one objective value, found {len(result)}")
    result["Variable"] = "Objective Function"
    result["Unit"] = "NZDb"
    result["Value"] = result["PV"] / 1_000
    return result[["Scenario", "Attribute", "Variable", "Unit", "Value"]]


def primary_energy(results: pd.DataFrame, metadata_dir: Path) -> pd.DataFrame:
    """Publish energy outputs from PREP-classified primary supply processes."""
    processes = _metadata(metadata_dir, "primary_production_processes.csv")
    fuels = _metadata(metadata_dir, "energy_commodities.csv")
    units = _metadata(metadata_dir, "process_units.csv").rename(
        columns={"techname": "Process", "tact": "Unit"}
    )[["Process", "Unit"]]
    result = results[results["Attribute"] == "VAR_FOut"].merge(
        processes, on="Process", how="inner"
    )
    result = result.merge(fuels, on="Commodity", how="inner").merge(
        units, on="Process", how="left"
    )
    result["Variable"] = "Primary Energy Production"
    return result.rename(columns={"PV": "Value"})


def batteries(results: pd.DataFrame, metadata_dir: Path) -> pd.DataFrame:
    """Publish battery capacity in the legacy capacity-output shape."""
    processes = _metadata(metadata_dir, "battery_processes.csv")
    result = results[results["Attribute"] == "VAR_Cap"].merge(
        processes, on="Process", how="inner", validate="many_to_one"
    )
    result["Variable"] = "Capacity"
    result["Unit"] = "GW"
    result = result.rename(columns={"PV": "Value"})
    return result[
        [
            "Scenario",
            "TechnologyGroup",
            "Technology",
            "Region",
            "Period",
            "TimeSlice",
            "Vintage",
            "Variable",
            "Unit",
            "Value",
        ]
    ]


def battery_flows(results: pd.DataFrame, metadata_dir: Path) -> pd.DataFrame:
    """Publish battery charge and discharge in the legacy flow-output shape."""
    processes = _metadata(metadata_dir, "battery_processes.csv")
    fuels = _metadata(metadata_dir, "energy_commodities.csv")
    result = results[results["Attribute"].isin(["VAR_FIn", "VAR_FOut"])].merge(
        processes, on="Process", how="inner", validate="many_to_one"
    )
    result = result.merge(fuels, on="Commodity", how="left", validate="many_to_one")
    result["Variable"] = result["Attribute"].map(
        {"VAR_FIn": "Battery charging", "VAR_FOut": "Battery discharging"}
    )
    result["Unit"] = "PJ"
    result = result.rename(columns={"PV": "Value"})
    return result[
        [
            "Scenario",
            "Attribute",
            "Variable",
            "Process",
            "TechnologyGroup",
            "Technology",
            "CommodityGroup",
            "Commodity",
            "Fuel",
            "Region",
            "Period",
            "TimeSlice",
            "Vintage",
            "Unit",
            "Value",
        ]
    ]


def demand_flex_flows(results: pd.DataFrame, metadata_dir: Path) -> pd.DataFrame:
    """Publish demand-flex inputs and outputs in the legacy flow shape."""
    processes = _metadata(metadata_dir, "demand_flex_processes.csv")
    result = results[results["Attribute"].isin(["VAR_FIn", "VAR_FOut"])].merge(
        processes, on="Process", how="inner", validate="many_to_one"
    )
    result["Variable"] = result["Attribute"].map(
        {"VAR_FIn": "Demand flex input", "VAR_FOut": "Demand flex output"}
    )
    result["CommodityGroup"] = "Demand flex intermediate"
    result["Fuel"] = "Demand flex"
    result["Unit"] = "PJ"
    result = result.rename(columns={"PV": "Value"})
    return result[
        [
            "Scenario",
            "Attribute",
            "Variable",
            "Process",
            "TechnologyGroup",
            "Technology",
            "CommodityGroup",
            "Commodity",
            "Fuel",
            "Region",
            "Period",
            "TimeSlice",
            "Vintage",
            "Unit",
            "Value",
        ]
    ]


def emissions(results: pd.DataFrame, metadata_dir: Path) -> pd.DataFrame:
    """Publish non-total emissions with available PREP process labels."""
    commodities = _metadata(metadata_dir, "emissions_commodities.csv")
    processes = pd.concat(
        [
            _metadata(metadata_dir, "demand_processes.csv"),
            _metadata(metadata_dir, "electricity_generation_processes.csv"),
            _metadata(metadata_dir, "primary_production_processes.csv"),
        ],
        ignore_index=True,
        sort=False,
    ).drop_duplicates("Process")
    result = results[
        (results["Attribute"] == "VAR_FOut") & (results["Commodity"] != "TOTCO2")
    ]
    result = result.merge(commodities, on="Commodity", how="inner").merge(
        processes, on="Process", how="left"
    )
    result["Unit"] = "kt CO2e"
    return result.rename(columns={"PV": "Value"})


def carbon_costs(results: pd.DataFrame) -> pd.DataFrame:
    """Publish total CO2, carbon cost, and implied carbon price."""
    base = results[results["Commodity"] == "TOTCO2"]
    keys = ["Scenario", "Period", "Region", "Commodity"]
    emissions_df = (
        base[base["Attribute"] == "VAR_FOut"]
        .groupby(keys, as_index=False)["PV"]
        .sum()
        .rename(columns={"PV": "Emissions_ktCO2"})
    )
    costs = (
        base[base["Attribute"] == "Cost_Comx"]
        .groupby(keys, as_index=False)["PV"]
        .sum()
        .rename(columns={"PV": "CarbonCost_MioNZD"})
    )
    result = emissions_df.merge(costs, on=keys, how="left").fillna(
        {"CarbonCost_MioNZD": 0}
    )
    result["ImpliedCarbonPrice_NZD_per_tCO2"] = (
        result["CarbonCost_MioNZD"].div(result["Emissions_ktCO2"]).mul(1000).fillna(0)
    )
    return result.melt(id_vars=keys, var_name="Variable", value_name="Value")


def postprocess_run(run_dir: Path, metadata_dir: Path) -> Path:
    """Write initial post-processing parquet outputs for one completed solver run."""
    files = sorted(run_dir.glob("*.vd"))
    if len(files) != 1:
        raise ValueError(
            f"Expected exactly one .vd file in {run_dir}, found {len(files)}"
        )
    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    scenario = _scenario_name(manifest, manifest_path)
    results = read_vd(files[0])
    results["Scenario"] = scenario
    output = run_dir / "postprocessed"
    output.mkdir(exist_ok=True)
    outputs = {
        "raw_results.parquet": results,
        "elec_generation.parquet": electricity_generation(results, metadata_dir),
        "energy_demand.parquet": energy_demand(results, metadata_dir),
        "energy_service_demand.parquet": energy_service_demand(results, metadata_dir),
        "electricity_demand_by_timeslice.parquet": electricity_demand_by_timeslice(
            results, metadata_dir
        ),
        "esd_by_timeslice.parquet": energy_service_demand_by_timeslice(
            results, metadata_dir
        ),
        "generation_by_timeslice.parquet": generation_by_timeslice(
            results, metadata_dir
        ),
        "transport_energy_demand.parquet": transport_energy_demand(
            results, metadata_dir
        ),
        "transport_energy_service_demand.parquet": transport_energy_service_demand(
            results, metadata_dir
        ),
        "transport_capacity.parquet": transport_capacity(results, metadata_dir),
        "technology_capacity.parquet": technology_capacity(results, metadata_dir),
        "objective_function.parquet": objective_function(results),
        "primary_energy.parquet": primary_energy(results, metadata_dir),
        "batteries.parquet": batteries(results, metadata_dir),
        "battery_flows.parquet": battery_flows(results, metadata_dir),
        "demand_flex_flows.parquet": demand_flex_flows(results, metadata_dir),
        "emissions.parquet": emissions(results, metadata_dir),
        "carbon_costs.parquet": carbon_costs(results),
    }
    for name, dataframe in outputs.items():
        dataframe.to_parquet(output / name, index=False)
    return output
