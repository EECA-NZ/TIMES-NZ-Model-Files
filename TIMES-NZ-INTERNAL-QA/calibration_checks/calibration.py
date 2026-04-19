"""
Compare postprocessed TIMES-NZ outputs against historical calibration data.

Currently includes:
- emissions by sector group
- industry total emissions by fuel
- raw EEUD demand by sector and fuel
- total emissions
- electricity consumption
- electricity generation
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

import pandas as pd

# pylint: disable = import-error
from times_nz_internal_qa.utilities.filepaths import FINAL_DATA, PREP_STAGE_2

BASE_DIR = Path(__file__).resolve().parent
CALIBRATION_DATA = BASE_DIR / "calibration_data"
CALIBRATION_RESULTS_FILE = BASE_DIR / "calibration_results.md"
GWH_PER_PJ = 277.77777778
GHG_INVENTORY_WORKBOOK = CALIBRATION_DATA / "ghg_inventory_2023.xlsx"


ASSESSMENT_YEARS = [2023]
MODELLED_GENERATION_CATEGORY_MAP = {
    "Hydro (Run-of-river)": "Hydro",
    "Hydro (Schedulable)": "Hydro",
    "Geothermal": "Geothermal",
    "Geothermal Cogen": "Geothermal",
    "Reciprocating Biogas": "Biogas",
    "Biogas Cogen": "Biogas",
    "Wood Cogen": "Wood",
    "Onshore wind": "Wind",
    "Distributed solar": "Solar",
    "Utility Solar (Tracking)": "Solar",
    "Diesel peaker": "Oil",
    "Coal Cogen": "Coal",
    "CCGT": "Gas",
    "Natural gas peaker": "Gas",
    "Natural gas cogen": "Gas",
}
RANKINE_FUEL_TO_GENERATION_CATEGORY_MAP = {
    "Coal": "Coal",
    "Natural gas": "Gas",
}
INVENTORY_SECTOR_GROUP_CODE_MAP = {
    "Agriculture, Forestry, and Fishing": "1.A.4.c. Agriculture-forestry",
    "Commercial": "1.A.4.a. Commercial-instituti",
    "Residential": "1.A.4.b. Residential",
    "Industry": "1.A.2. Manufacturing industri",
    "Transport": "1.A.3. Transport",
    "Electricity generation": "1.A.1.a. Public electricity a",
    "Fugitive emissions": "1.B. Fugitive emissions from ",
}
INDUSTRY_FUEL_CODE_MAP = {
    "NGA": "Gaseous fuels",
    "COA": "Solid fuels",
    "DSL": "Liquid fuels",
    "FOL": "Liquid fuels",
    "LPG": "Liquid fuels",
    "PET": "Liquid fuels",
}
INVENTORY_INDUSTRY_FUEL_NAMES = [
    "Biomass",
    "Gaseous fuels",
    "Liquid fuels",
    "Other fossil fuels",
    "Solid fuels",
]
RAW_EEUD_BASEYEAR_FILES = [
    (
        PREP_STAGE_2 / "industry/preprocessing/1_times_eeud_alignment_baseyear.csv",
        "Industry",
    ),
    (
        PREP_STAGE_2 / "commercial/preprocessing/1_times_eeud_alignment_baseyear.csv",
        "Commercial",
    ),
    (
        PREP_STAGE_2
        / "ag_forest_fish/preprocessing/1_times_eeud_alignment_baseyear.csv",
        "Agriculture, Forestry, and Fishing",
    ),
]
RAW_EEUD_FUEL_MAP = {
    "Natural gas": "Natural Gas",
    "Fuel oil": "Fuel Oil",
    "Wood residuals (onsite)": "Wood",
}


def get_times_data(filename):
    """Read postprocessed TIMES data."""
    return pd.read_parquet(FINAL_DATA / filename)


def excel_column_index(cell_reference):
    """Convert an Excel cell reference like AB12 to a zero-based column index."""
    letters = "".join(char for char in str(cell_reference) if char.isalpha())
    index = 0
    for char in letters:
        index = index * 26 + (ord(char.upper()) - 64)
    return index - 1


def build_shared_strings(workbook, spreadsheet_ns):
    """Return the workbook shared strings table."""
    shared_strings_root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
    return [
        "".join(
            text_node.text or ""
            for text_node in string_item.iterfind(".//main:t", spreadsheet_ns)
        )
        for string_item in shared_strings_root.findall("main:si", spreadsheet_ns)
    ]


def get_worksheet_target(workbook, sheet_name, spreadsheet_ns):
    """Return the internal xlsx path for a worksheet name."""
    workbook_root = ET.fromstring(workbook.read("xl/workbook.xml"))
    workbook_rels_root = ET.fromstring(workbook.read("xl/_rels/workbook.xml.rels"))
    workbook_rel_map = {
        relationship.attrib["Id"]: relationship.attrib["Target"]
        for relationship in workbook_rels_root
    }

    for sheet in workbook_root.find("main:sheets", spreadsheet_ns):
        rel_id = sheet.attrib[
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
        ]
        if sheet.attrib["name"] == sheet_name:
            return workbook_rel_map[rel_id]

    raise ValueError(f"Worksheet '{sheet_name}' not found")


def get_cell_text(cell, shared_strings, spreadsheet_ns):
    """Extract text from a worksheet cell."""
    cell_type = cell.attrib.get("t")
    value_node = cell.find("main:v", spreadsheet_ns)
    if value_node is None:
        return "".join(
            text_node.text or ""
            for text_node in cell.iterfind(".//main:t", spreadsheet_ns)
        )

    cell_text = value_node.text or ""
    if cell_type == "s":
        return shared_strings[int(cell_text)]
    return cell_text


def parse_worksheet_rows(sheet_data, shared_strings, spreadsheet_ns):
    """Expand worksheet rows into a list of string lists."""
    rows = []
    for row in sheet_data.findall("main:row", spreadsheet_ns):
        values_by_column = {}
        for cell in row.findall("main:c", spreadsheet_ns):
            cell_reference = cell.attrib.get("r", "")
            values_by_column[excel_column_index(cell_reference)] = get_cell_text(
                cell, shared_strings, spreadsheet_ns
            )

        if values_by_column:
            max_column = max(values_by_column)
            rows.append(
                [values_by_column.get(index, "") for index in range(max_column + 1)]
            )
    return rows


def get_workbook_sheet_rows(workbook_path, sheet_name):
    """Read a worksheet from an xlsx workbook without requiring openpyxl."""
    spreadsheet_ns = {
        "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    }

    with ZipFile(workbook_path) as workbook:
        shared_strings = build_shared_strings(workbook, spreadsheet_ns)
        worksheet_target = get_worksheet_target(workbook, sheet_name, spreadsheet_ns)
        worksheet_root = ET.fromstring(workbook.read(f"xl/{worksheet_target}"))
        sheet_data = worksheet_root.find("main:sheetData", spreadsheet_ns)
        return parse_worksheet_rows(sheet_data, shared_strings, spreadsheet_ns)


def get_inventory_emissions():
    """Load the 2023 all-gases inventory workbook and return a long table."""
    rows = get_workbook_sheet_rows(GHG_INVENTORY_WORKBOOK, "All gases")
    header = rows[10]
    period_columns = [column for column in header[2:] if str(column).isdigit()]

    records = []
    for row in rows[11:]:
        inventory_code = row[0] if len(row) > 0 else ""
        inventory_name = row[1].strip() if len(row) > 1 else ""
        if not inventory_code:
            continue
        for offset, period in enumerate(period_columns, start=2):
            value = row[offset] if len(row) > offset else ""
            records.append(
                {
                    "InventoryCode": inventory_code.strip(),
                    "InventoryName": inventory_name,
                    "Period": pd.to_numeric(period, errors="coerce"),
                    "HistoricalValue": pd.to_numeric(value, errors="coerce"),
                }
            )

    df = pd.DataFrame.from_records(records)
    df = df.dropna(subset=["Period", "HistoricalValue"])
    df["Period"] = df["Period"].astype(int)
    return df


def get_inventory_total_emissions():
    """Return the 2023 inventory total for the Energy chapter."""
    inventory = get_inventory_emissions()
    return inventory[inventory["InventoryCode"] == "1. Energy"][
        ["Period", "HistoricalValue"]
    ].rename(columns={"HistoricalValue": "InventoryTotal"})


def get_model_scenarios():
    """Return the scenario names present in the model outputs."""
    return sorted(get_times_data("energy_demand.parquet")["Scenario"].unique())


def get_inventory_industry_emissions():
    """Return inventory emissions for the industry chapter."""
    inventory = get_inventory_emissions()
    return inventory[
        inventory["InventoryCode"].str.startswith("1.A.2", na=False)
    ].copy()


def get_raw_eeud_columns(df, sector_group):
    """Standardize raw EEUD baseyear columns across source files."""
    out = df.copy()
    if "Year" in out.columns:
        out = out.rename(columns={"Year": "Period"})
    elif "Period" not in out.columns:
        out["Period"] = 2023
    out["SectorGroup"] = sector_group
    out["Period"] = pd.to_numeric(out["Period"], errors="coerce").astype("Int64")
    out["HistoricalValue"] = pd.to_numeric(out["Value"], errors="coerce")
    out["Fuel"] = out["Fuel"].replace(RAW_EEUD_FUEL_MAP)
    return out[["SectorGroup", "Sector", "Fuel", "Period", "HistoricalValue"]]


def load_raw_eeud_baseyear_file(path, sector_group):
    """Load one raw EEUD baseyear file and standardize its columns."""
    return get_raw_eeud_columns(pd.read_csv(path), sector_group)


def get_raw_eeud_demand():
    """Return raw EEUD-aligned 2023 demand values by sector and fuel."""
    tables = [
        load_raw_eeud_baseyear_file(path, sector_group)
        for path, sector_group in RAW_EEUD_BASEYEAR_FILES
    ]
    demand = pd.concat(tables, ignore_index=True)
    demand = demand.dropna(subset=["Period", "HistoricalValue"])
    return (
        demand.groupby(["SectorGroup", "Sector", "Fuel", "Period"], as_index=False)[
            "HistoricalValue"
        ]
        .sum()
        .sort_values(["SectorGroup", "Sector", "Fuel", "Period"])
    )


def get_inventory_sector_group_emissions():
    """Return inventory emissions by top-level sector group."""
    inventory = get_inventory_emissions()
    rows = []
    for sector_group, inventory_code in INVENTORY_SECTOR_GROUP_CODE_MAP.items():
        sector_inventory = inventory[
            inventory["InventoryCode"] == inventory_code
        ].copy()
        if sector_inventory.empty:
            continue
        sector_inventory["SectorGroup"] = sector_group
        rows.append(sector_inventory[["SectorGroup", "Period", "HistoricalValue"]])
    return pd.concat(rows, ignore_index=True).sort_values(["SectorGroup", "Period"])


def get_inventory_industry_emissions_by_fuel():
    """Return inventory industry emissions aggregated to fuel groups."""
    inventory = get_inventory_industry_emissions()
    inventory = inventory[
        inventory["InventoryName"].isin(INVENTORY_INDUSTRY_FUEL_NAMES)
    ].copy()
    return (
        inventory.groupby(["InventoryName", "Period"], as_index=False)[
            "HistoricalValue"
        ]
        .sum()
        .rename(columns={"InventoryName": "FuelGroup"})
        .sort_values(["FuelGroup", "Period"])
    )


def get_modelled_sector_group_emissions():
    """Return model emissions by sector group."""
    emissions = get_times_data("emissions.parquet")
    return (
        emissions.groupby(["Scenario", "SectorGroup", "Period"], as_index=False)[
            "Value"
        ]
        .sum()
        .rename(columns={"Value": "ModelledValue"})
        .sort_values(["SectorGroup", "Scenario", "Period"])
    )


def get_modelled_eeud_demand():
    """Return model demand for the EEUD-aligned sectors by sector and fuel."""
    demand = get_times_data("energy_demand.parquet").copy()
    eeud_sector_groups = [sector_group for _, sector_group in RAW_EEUD_BASEYEAR_FILES]
    demand = demand[demand["SectorGroup"].isin(eeud_sector_groups)].copy()
    demand["Fuel"] = demand["Fuel"].replace(RAW_EEUD_FUEL_MAP)
    return (
        demand.groupby(
            ["Scenario", "SectorGroup", "Sector", "Fuel", "Period"], as_index=False
        )["Value"]
        .sum()
        .rename(columns={"Value": "ModelledValue"})
        .sort_values(["SectorGroup", "Sector", "Fuel", "Scenario", "Period"])
    )


def get_process_fuel_group(process_name):
    """Map a TIMES process name to the industry fuel groups used in the inventory."""
    fuel_code = str(process_name).split("-")[1] if "-" in str(process_name) else None
    return INDUSTRY_FUEL_CODE_MAP.get(fuel_code)


def get_modelled_industry_emissions_by_fuel():
    """Return modelled industry emissions aggregated to inventory-like fuel groups."""
    emissions = get_times_data("emissions.parquet")
    emissions = emissions[emissions["SectorGroup"] == "Industry"].copy()
    emissions["FuelGroup"] = emissions["Process"].map(get_process_fuel_group)
    emissions = emissions[emissions["FuelGroup"].notna()].copy()
    return (
        emissions.groupby(["Scenario", "FuelGroup", "Period"], as_index=False)["Value"]
        .sum()
        .rename(columns={"Value": "ModelledValue"})
        .sort_values(["FuelGroup", "Scenario", "Period"])
    )


def build_emissions_comparison():
    """Return emissions comparison by sector group."""
    historical = get_inventory_sector_group_emissions()
    modelled = get_modelled_sector_group_emissions()

    scenarios = pd.DataFrame({"Scenario": sorted(modelled["Scenario"].unique())})
    comparison_index = historical[["SectorGroup", "Period", "HistoricalValue"]].copy()
    comparison_index["key"] = 1
    scenarios["key"] = 1
    comparison = comparison_index.merge(scenarios, on="key", how="left").drop(
        columns="key"
    )
    comparison = comparison.merge(
        modelled[["SectorGroup", "Scenario", "Period", "ModelledValue"]],
        on=["SectorGroup", "Scenario", "Period"],
        how="left",
    )
    comparison["ModelledValue"] = comparison["ModelledValue"].fillna(0)
    comparison["Difference"] = (
        comparison["ModelledValue"] - comparison["HistoricalValue"]
    )
    comparison["PercentDifference"] = (
        comparison["Difference"].where(comparison["HistoricalValue"] != 0)
        / comparison["HistoricalValue"].where(comparison["HistoricalValue"] != 0)
        * 100
    )
    return comparison[
        [
            "SectorGroup",
            "Scenario",
            "Period",
            "HistoricalValue",
            "ModelledValue",
            "Difference",
            "PercentDifference",
        ]
    ].sort_values(["SectorGroup", "Scenario", "Period"])


def build_total_emissions_comparison():
    """Return total emissions comparison."""
    inventory_total = get_inventory_total_emissions()
    modelled_total = (
        get_times_data("emissions.parquet")
        .groupby(["Scenario", "Period"], as_index=False)["Value"]
        .sum()
        .rename(columns={"Value": "ModelledValue"})
    )
    comparison = modelled_total.merge(inventory_total, on="Period", how="left")
    comparison = comparison.rename(columns={"InventoryTotal": "HistoricalValue"})
    comparison["Difference"] = (
        comparison["ModelledValue"] - comparison["HistoricalValue"]
    )
    comparison["PercentDifference"] = (
        comparison["Difference"].where(comparison["HistoricalValue"] != 0)
        / comparison["HistoricalValue"].where(comparison["HistoricalValue"] != 0)
        * 100
    )
    return comparison[
        [
            "Scenario",
            "Period",
            "HistoricalValue",
            "ModelledValue",
            "Difference",
            "PercentDifference",
        ]
    ].sort_values(["Scenario", "Period"])


def build_industry_emissions_by_fuel_comparison():
    """Return industry total emissions compared by fuel group."""
    historical = get_inventory_industry_emissions_by_fuel()
    modelled = get_modelled_industry_emissions_by_fuel()

    scenarios = pd.DataFrame({"Scenario": sorted(modelled["Scenario"].unique())})
    comparison_index = historical[["FuelGroup", "Period", "HistoricalValue"]].copy()
    comparison_index["key"] = 1
    scenarios["key"] = 1
    comparison = comparison_index.merge(scenarios, on="key", how="left").drop(
        columns="key"
    )
    comparison = comparison.merge(
        modelled[["FuelGroup", "Scenario", "Period", "ModelledValue"]],
        on=["FuelGroup", "Scenario", "Period"],
        how="left",
    )
    comparison["ModelledValue"] = comparison["ModelledValue"].fillna(0)
    comparison["Difference"] = (
        comparison["ModelledValue"] - comparison["HistoricalValue"]
    )
    comparison["PercentDifference"] = (
        comparison["Difference"].where(comparison["HistoricalValue"] != 0)
        / comparison["HistoricalValue"].where(comparison["HistoricalValue"] != 0)
        * 100
    )
    return comparison[
        [
            "FuelGroup",
            "Scenario",
            "Period",
            "HistoricalValue",
            "ModelledValue",
            "Difference",
            "PercentDifference",
        ]
    ].sort_values(["FuelGroup", "Scenario", "Period"])


def add_scenarios_to_historical(df, scenarios):
    """Cross join a historical table to all model scenarios."""
    scenario_df = pd.DataFrame({"Scenario": scenarios})
    out = df.copy()
    out["key"] = 1
    scenario_df["key"] = 1
    return out.merge(scenario_df, on="key", how="left").drop(columns="key")


def build_raw_eeud_demand_comparison():
    """Return raw EEUD demand compared with model demand by sector and fuel."""
    historical = add_scenarios_to_historical(
        get_raw_eeud_demand(), get_model_scenarios()
    )
    modelled = get_modelled_eeud_demand()
    comparison = historical.merge(
        modelled,
        on=["Scenario", "SectorGroup", "Sector", "Fuel", "Period"],
        how="outer",
    )
    comparison["HistoricalValue"] = comparison["HistoricalValue"].fillna(0)
    comparison["ModelledValue"] = comparison["ModelledValue"].fillna(0)
    comparison["Difference"] = (
        comparison["ModelledValue"] - comparison["HistoricalValue"]
    )
    comparison["PercentDifference"] = (
        comparison["Difference"].where(comparison["HistoricalValue"] != 0)
        / comparison["HistoricalValue"].where(comparison["HistoricalValue"] != 0)
        * 100
    )
    comparison["AbsoluteDifference"] = comparison["Difference"].abs()
    return (
        comparison[
            [
                "SectorGroup",
                "Sector",
                "Fuel",
                "Scenario",
                "Period",
                "HistoricalValue",
                "ModelledValue",
                "Difference",
                "PercentDifference",
            ]
        ]
        .assign(AbsoluteDifference=comparison["AbsoluteDifference"])
        .sort_values(
            [
                "AbsoluteDifference",
                "SectorGroup",
                "Sector",
                "Fuel",
                "Scenario",
                "Period",
            ],
            ascending=[False, True, True, True, True, True],
        )
        .drop(columns="AbsoluteDifference")
    )


def build_raw_eeud_sector_total_comparison(raw_eeud_demand_comparison):
    """Roll raw EEUD demand comparison up to sector totals."""
    comparison = raw_eeud_demand_comparison.groupby(
        ["SectorGroup", "Sector", "Scenario", "Period"], as_index=False
    )[["HistoricalValue", "ModelledValue"]].sum()
    comparison["Difference"] = (
        comparison["ModelledValue"] - comparison["HistoricalValue"]
    )
    comparison["PercentDifference"] = (
        comparison["Difference"].where(comparison["HistoricalValue"] != 0)
        / comparison["HistoricalValue"].where(comparison["HistoricalValue"] != 0)
        * 100
    )
    comparison["AbsoluteDifference"] = comparison["Difference"].abs()
    return (
        comparison[
            [
                "SectorGroup",
                "Sector",
                "Scenario",
                "Period",
                "HistoricalValue",
                "ModelledValue",
                "Difference",
                "PercentDifference",
            ]
        ]
        .assign(AbsoluteDifference=comparison["AbsoluteDifference"])
        .sort_values(
            ["AbsoluteDifference", "SectorGroup", "Sector", "Scenario", "Period"],
            ascending=[False, True, True, True, True],
        )
        .drop(columns="AbsoluteDifference")
    )


def get_historical_electricity_consumption():
    """
    Load historical electricity consumption and align it with model sectors.

    Historical unallocated onsite consumption is compared as part of industrial
    demand because that load is assigned to industry in the model outputs.
    """
    df = pd.read_csv(CALIBRATION_DATA / "electricity.csv")
    df = df[df["Category"] == "Consumption"].copy()
    df = df.melt(
        id_vars=["Category", "sector", "Unit"],
        var_name="Period",
        value_name="HistoricalValue",
    )
    df["Period"] = pd.to_numeric(df["Period"], errors="coerce")
    df["HistoricalValue"] = pd.to_numeric(df["HistoricalValue"], errors="coerce")
    df = df.dropna(subset=["Period", "HistoricalValue"])

    onsite = df[df["sector"] == "Unallocated onsite consumption"].copy()
    if not onsite.empty:
        onsite["sector"] = "Industrial"
        df = pd.concat(
            [df[df["sector"] != "Unallocated onsite consumption"], onsite],
            ignore_index=True,
        )

    return (
        df.groupby(["sector", "Period", "Unit"], as_index=False)["HistoricalValue"]
        .sum()
        .rename(columns={"sector": "Sector"})
    )


def get_historical_electricity_generation():
    """Load historical electricity generation in MBIE categories."""
    df = pd.read_csv(CALIBRATION_DATA / "electricity.csv")
    df = df[df["Category"] == "Net generation"].copy()
    df = df.melt(
        id_vars=["Category", "sector", "Unit"],
        var_name="Period",
        value_name="HistoricalValue",
    )
    df["Period"] = pd.to_numeric(df["Period"], errors="coerce")
    df["HistoricalValue"] = pd.to_numeric(df["HistoricalValue"], errors="coerce")
    df = df.dropna(subset=["Period", "HistoricalValue"])
    return df.rename(columns={"sector": "GenerationCategory"})


def get_modelled_electricity_consumption():
    """Aggregate modelled electricity consumption to match the historical sectors."""
    df = get_times_data("energy_demand.parquet")
    df = df[df["Fuel"] == "Electricity"].copy()

    sector_map = {
        "Agriculture, Forestry, and Fishing": "Agriculture, Forestry, and Fishing",
        "Industry": "Industrial",
        "Commercial": "Commercial",
        "Residential": "Residential",
        "Transport": "Transport",
    }
    df["Sector"] = df["SectorGroup"].map(sector_map)
    df = df[df["Sector"].notna()].copy()

    modelled = (
        df.groupby(["Scenario", "Sector", "Period"], as_index=False)["Value"]
        .sum()
        .rename(columns={"Value": "ModelledValue"})
    )
    modelled["ModelledValue"] = modelled["ModelledValue"] * GWH_PER_PJ
    return modelled


def get_modelled_electricity_generation():
    """
    Aggregate modelled electricity generation to MBIE categories.

    Rankine output is split between Coal and Gas using the modelled Rankine
    fuel-use shares for each scenario and period.
    """
    df = get_times_data("elec_generation.parquet")
    generation = df[df["Variable"] == "Electricity generation"].copy()
    rankine_generation = generation[generation["Technology"] == "Rankine"].copy()
    non_rankine_generation = generation[generation["Technology"] != "Rankine"].copy()

    non_rankine_generation["GenerationCategory"] = non_rankine_generation[
        "Technology"
    ].map(MODELLED_GENERATION_CATEGORY_MAP)

    unmapped = (
        non_rankine_generation[non_rankine_generation["GenerationCategory"].isna()][
            "Technology"
        ]
        .dropna()
        .drop_duplicates()
        .tolist()
    )
    if unmapped:
        print(
            "Unmapped electricity generation technologies excluded from calibration:",
            ", ".join(sorted(unmapped)),
        )

    non_rankine_generation = non_rankine_generation[
        non_rankine_generation["GenerationCategory"].notna()
    ].copy()
    non_rankine_generation = (
        non_rankine_generation.groupby(
            ["Scenario", "GenerationCategory", "Period"], as_index=False
        )["Value"]
        .sum()
        .rename(columns={"Value": "ModelledValue"})
    )
    rankine_fuel_use = df[df["Variable"] == "Electricity fuel use"].copy()
    rankine_fuel_use = rankine_fuel_use[
        rankine_fuel_use["Technology"] == "Rankine"
    ].copy()
    rankine_fuel_use["GenerationCategory"] = rankine_fuel_use["Fuel"].map(
        RANKINE_FUEL_TO_GENERATION_CATEGORY_MAP
    )
    rankine_fuel_use = rankine_fuel_use[
        rankine_fuel_use["GenerationCategory"].notna()
    ].copy()
    rankine_fuel_use = rankine_fuel_use.groupby(
        ["Scenario", "Period", "GenerationCategory"], as_index=False
    )["Value"].sum()
    rankine_totals = rankine_fuel_use.groupby(["Scenario", "Period"], as_index=False)[
        "Value"
    ].sum()
    rankine_totals = rankine_totals.rename(columns={"Value": "RankineFuelTotal"})
    rankine_fuel_use = rankine_fuel_use.merge(
        rankine_totals,
        on=["Scenario", "Period"],
        how="left",
    )
    rankine_fuel_use["RankineShare"] = (
        rankine_fuel_use["Value"] / rankine_fuel_use["RankineFuelTotal"]
    )

    rankine_generation = rankine_generation.groupby(
        ["Scenario", "Period"], as_index=False
    )["Value"].sum()
    rankine_generation = rankine_generation.merge(
        rankine_fuel_use[["Scenario", "Period", "GenerationCategory", "RankineShare"]],
        on=["Scenario", "Period"],
        how="left",
    )
    rankine_generation = rankine_generation[
        rankine_generation["GenerationCategory"].notna()
    ].copy()
    rankine_generation["ModelledValue"] = (
        rankine_generation["Value"] * rankine_generation["RankineShare"]
    )
    rankine_generation = rankine_generation[
        ["Scenario", "GenerationCategory", "Period", "ModelledValue"]
    ]

    modelled = pd.concat(
        [non_rankine_generation, rankine_generation],
        ignore_index=True,
    )
    modelled = modelled.groupby(
        ["Scenario", "GenerationCategory", "Period"], as_index=False
    )["ModelledValue"].sum()
    modelled["ModelledValue"] = modelled["ModelledValue"] * GWH_PER_PJ
    return modelled


def build_electricity_consumption_comparison():
    """Return the electricity consumption calibration comparison table."""
    historical = get_historical_electricity_consumption()
    modelled = get_modelled_electricity_consumption()

    historical_years = sorted(historical["Period"].unique())
    modelled = modelled[modelled["Period"].isin(historical_years)].copy()

    comparison = modelled.merge(
        historical[["Sector", "Period", "HistoricalValue"]],
        on=["Sector", "Period"],
        how="inner",
    )

    comparison["Difference"] = (
        comparison["ModelledValue"] - comparison["HistoricalValue"]
    )
    comparison["PercentDifference"] = (
        comparison["Difference"] / comparison["HistoricalValue"] * 100
    )

    comparison = comparison[
        [
            "Sector",
            "Scenario",
            "Period",
            "HistoricalValue",
            "ModelledValue",
            "Difference",
            "PercentDifference",
        ]
    ].sort_values(["Scenario", "Sector", "Period"])

    return comparison


def build_total_electricity_consumption_comparison(electricity_consumption_comparison):
    """Return a total electricity consumption comparison table."""
    comparison = (
        electricity_consumption_comparison.groupby(
            ["Scenario", "Period"], as_index=False
        )[["HistoricalValue", "ModelledValue"]]
        .sum()
        .assign(Metric="Total electricity consumption")
    )
    comparison["Difference"] = (
        comparison["ModelledValue"] - comparison["HistoricalValue"]
    )
    comparison["PercentDifference"] = (
        comparison["Difference"] / comparison["HistoricalValue"] * 100
    )
    return comparison[
        [
            "Metric",
            "Scenario",
            "Period",
            "HistoricalValue",
            "ModelledValue",
            "Difference",
            "PercentDifference",
        ]
    ].sort_values(["Period", "Scenario"])


def build_electricity_generation_comparison():
    """Return the electricity generation calibration comparison table."""
    historical = get_historical_electricity_generation()
    modelled = get_modelled_electricity_generation()

    historical_years = sorted(historical["Period"].unique())
    modelled = modelled[modelled["Period"].isin(historical_years)].copy()
    scenarios = pd.DataFrame({"Scenario": sorted(modelled["Scenario"].unique())})
    historical_index = historical[
        ["GenerationCategory", "Period", "HistoricalValue"]
    ].copy()
    historical_index["key"] = 1
    scenarios["key"] = 1
    comparison = historical_index.merge(scenarios, on="key", how="left").drop(
        columns="key"
    )
    comparison = comparison.merge(
        modelled[["Scenario", "GenerationCategory", "Period", "ModelledValue"]],
        on=["Scenario", "GenerationCategory", "Period"],
        how="left",
    )
    comparison["ModelledValue"] = comparison["ModelledValue"].fillna(0)

    comparison["Difference"] = (
        comparison["ModelledValue"] - comparison["HistoricalValue"]
    )
    comparison["PercentDifference"] = (
        comparison["Difference"] / comparison["HistoricalValue"] * 100
    )

    comparison = comparison[
        [
            "GenerationCategory",
            "Scenario",
            "Period",
            "HistoricalValue",
            "ModelledValue",
            "Difference",
            "PercentDifference",
        ]
    ].sort_values(["Scenario", "GenerationCategory", "Period"])

    return comparison


def build_total_generation_comparison(electricity_generation_comparison):
    """Return a total electricity generation comparison table."""
    comparison = (
        electricity_generation_comparison.groupby(
            ["Scenario", "Period"], as_index=False
        )[["HistoricalValue", "ModelledValue"]]
        .sum()
        .assign(Metric="Total generation")
    )
    comparison["Difference"] = (
        comparison["ModelledValue"] - comparison["HistoricalValue"]
    )
    comparison["PercentDifference"] = (
        comparison["Difference"] / comparison["HistoricalValue"] * 100
    )
    return comparison[
        [
            "Metric",
            "Scenario",
            "Period",
            "HistoricalValue",
            "ModelledValue",
            "Difference",
            "PercentDifference",
        ]
    ].sort_values(["Period", "Scenario"])


def format_table(df):
    """Format numeric columns for console-friendly table output."""
    out = df.copy()
    for col in ["HistoricalValue", "ModelledValue", "Difference"]:
        if col in out.columns:
            out[col] = out[col].map(lambda value: f"{value:,.2f}")
    if "PercentDifference" in out.columns:
        out["PercentDifference"] = out["PercentDifference"].map(
            lambda value: f"{value:,.2f}%"
        )
    return out


def dataframe_to_markdown(df):
    """Render a dataframe as a simple markdown table."""
    if df.empty:
        return "_No rows_\n"

    markdown_df = df.fillna("nan")
    columns = [str(column) for column in markdown_df.columns]
    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = [
        "| " + " | ".join(str(value) for value in row) + " |"
        for row in markdown_df.itertuples(index=False, name=None)
    ]
    return "\n".join([header, divider, *rows]) + "\n"


def filter_assessment_years(df):
    """Restrict output rows to configured assessment years."""
    if not ASSESSMENT_YEARS:
        return df
    return df[df["Period"].isin(ASSESSMENT_YEARS)].copy()


def main():
    """Run calibration comparisons and write a markdown report."""
    emissions_comparison = build_emissions_comparison()
    industry_emissions_by_fuel_comparison = (
        build_industry_emissions_by_fuel_comparison()
    )
    raw_eeud_demand_comparison = build_raw_eeud_demand_comparison()
    raw_eeud_sector_total_comparison = build_raw_eeud_sector_total_comparison(
        raw_eeud_demand_comparison
    )
    total_emissions_comparison = build_total_emissions_comparison()
    electricity_consumption_comparison = build_electricity_consumption_comparison()
    total_electricity_consumption_comparison = (
        build_total_electricity_consumption_comparison(
            electricity_consumption_comparison
        )
    )
    electricity_generation_comparison = build_electricity_generation_comparison()
    total_generation_comparison = build_total_generation_comparison(
        electricity_generation_comparison
    )
    emissions_comparison = filter_assessment_years(emissions_comparison)
    industry_emissions_by_fuel_comparison = filter_assessment_years(
        industry_emissions_by_fuel_comparison
    )
    raw_eeud_demand_comparison = filter_assessment_years(raw_eeud_demand_comparison)
    raw_eeud_sector_total_comparison = filter_assessment_years(
        raw_eeud_sector_total_comparison
    )
    total_emissions_comparison = filter_assessment_years(total_emissions_comparison)
    electricity_consumption_comparison = filter_assessment_years(
        electricity_consumption_comparison
    )
    total_electricity_consumption_comparison = filter_assessment_years(
        total_electricity_consumption_comparison
    )
    electricity_generation_comparison = filter_assessment_years(
        electricity_generation_comparison
    )
    total_generation_comparison = filter_assessment_years(total_generation_comparison)
    sections = [
        ("Emissions by sector group", format_table(emissions_comparison)),
        (
            "Industry emissions by fuel",
            format_table(industry_emissions_by_fuel_comparison),
        ),
        (
            "Raw EEUD demand by sector and fuel",
            format_table(raw_eeud_demand_comparison),
        ),
        ("Raw EEUD demand by sector", format_table(raw_eeud_sector_total_comparison)),
        ("Total emissions", format_table(total_emissions_comparison)),
        ("Electricity consumption", format_table(electricity_consumption_comparison)),
        (
            "Total electricity consumption",
            format_table(total_electricity_consumption_comparison),
        ),
        ("Electricity generation", format_table(electricity_generation_comparison)),
        ("Total generation", format_table(total_generation_comparison)),
    ]

    markdown_parts = ["# Calibration Results", ""]
    for title, dataframe in sections:
        markdown_parts.append(f"## {title}")
        markdown_parts.append("")
        markdown_parts.append(dataframe_to_markdown(dataframe))

    CALIBRATION_RESULTS_FILE.write_text(
        "\n".join(markdown_parts).strip() + "\n",
        encoding="utf-8",
    )
    print(f"Calibration results written to {CALIBRATION_RESULTS_FILE}")


if __name__ == "__main__":
    main()
