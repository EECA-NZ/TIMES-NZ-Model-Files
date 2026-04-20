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
    "Fugitive emissions": "1.B. Fugitive emissions from",
}
GEOTHERMAL_FUGITIVE_CODE = "1.B.2.d. Geothermal"
DISPLAY_ZERO_DECIMALS = 2
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
SPREADSHEET_NS = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
FORMAT_COLUMNS = ["HistoricalValue", "ModelledValue", "Difference"]


def get_times_data(filename):
    """Read postprocessed TIMES data."""
    return pd.read_parquet(FINAL_DATA / filename)


def excel_column_index(cell_reference):
    """Convert an Excel cell reference like AB12 to a zero-based column index."""
    index = 0
    for char in "".join(char for char in str(cell_reference) if char.isalpha()):
        index = index * 26 + (ord(char.upper()) - 64)
    return index - 1


def get_shared_strings(workbook):
    """Return workbook shared strings."""
    shared_strings_root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
    return [
        "".join(
            text_node.text or ""
            for text_node in string_item.iterfind(".//main:t", SPREADSHEET_NS)
        )
        for string_item in shared_strings_root.findall("main:si", SPREADSHEET_NS)
    ]


def get_worksheet_target(workbook, sheet_name):
    """Return the internal xlsx path for a worksheet name."""
    workbook_root = ET.fromstring(workbook.read("xl/workbook.xml"))
    workbook_rels_root = ET.fromstring(workbook.read("xl/_rels/workbook.xml.rels"))
    worksheet_targets = {
        relationship.attrib["Id"]: relationship.attrib["Target"]
        for relationship in workbook_rels_root
    }
    worksheet_target = next(
        (
            worksheet_targets[
                sheet.attrib[
                    "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
                ]
            ]
            for sheet in workbook_root.find("main:sheets", SPREADSHEET_NS)
            if sheet.attrib["name"] == sheet_name
        ),
        None,
    )
    if worksheet_target is None:
        raise ValueError(f"Worksheet '{sheet_name}' not found")
    return worksheet_target


def get_cell_value(cell, shared_strings):
    """Return the text value for an xlsx cell."""
    value_node = cell.find("main:v", SPREADSHEET_NS)
    if value_node is None:
        return "".join(
            text_node.text or ""
            for text_node in cell.iterfind(".//main:t", SPREADSHEET_NS)
        )

    value = value_node.text or ""
    if cell.attrib.get("t") == "s":
        return shared_strings[int(value)]
    return value


def parse_sheet_rows(sheet_data, shared_strings):
    """Parse an xlsx sheet into a list of row values."""
    rows = []
    for row in sheet_data.findall("main:row", SPREADSHEET_NS):
        values_by_column = {
            excel_column_index(cell.attrib.get("r", "")): get_cell_value(
                cell, shared_strings
            )
            for cell in row.findall("main:c", SPREADSHEET_NS)
        }
        if values_by_column:
            rows.append(
                [
                    values_by_column.get(index, "")
                    for index in range(max(values_by_column) + 1)
                ]
            )
    return rows


def get_workbook_sheet_rows(workbook_path, sheet_name):
    """Read a worksheet from an xlsx workbook without requiring openpyxl."""

    with ZipFile(workbook_path) as workbook:
        shared_strings = get_shared_strings(workbook)
        worksheet_target = get_worksheet_target(workbook, sheet_name)
        worksheet_root = ET.fromstring(workbook.read(f"xl/{worksheet_target}"))
        sheet_data = worksheet_root.find("main:sheetData", SPREADSHEET_NS)
        return parse_sheet_rows(sheet_data, shared_strings)


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


def calculate_differences(df):
    """Add absolute and percentage difference columns to a comparison table."""
    out = df.copy()
    out["Difference"] = out["ModelledValue"] - out["HistoricalValue"]
    out["PercentDifference"] = (
        out["Difference"].where(out["HistoricalValue"] != 0)
        / out["HistoricalValue"].where(out["HistoricalValue"] != 0)
        * 100
    )
    return out


def cross_join_scenarios(df, scenarios):
    """Duplicate historical rows for each model scenario."""
    scenario_df = pd.DataFrame({"Scenario": scenarios})
    return (
        df.assign(key=1).merge(scenario_df.assign(key=1), on="key").drop(columns="key")
    )


def build_scenario_comparison(
    historical, modelled, key_columns, sort_columns, output_columns
):
    """Compare historical values against modelled values for each scenario."""
    comparison = cross_join_scenarios(historical, sorted(modelled["Scenario"].unique()))
    comparison = comparison.merge(
        modelled[key_columns + ["Scenario", "ModelledValue"]],
        on=key_columns + ["Scenario"],
        how="left",
    )
    comparison["ModelledValue"] = comparison["ModelledValue"].fillna(0)
    return calculate_differences(comparison)[output_columns].sort_values(sort_columns)


def build_total_comparison(df, output_columns, metric=None):
    """Roll a comparison table up to scenario-period totals."""
    comparison = df.groupby(["Scenario", "Period"], as_index=False)[
        ["HistoricalValue", "ModelledValue"]
    ].sum()
    if metric is not None:
        comparison["Metric"] = metric
    return calculate_differences(comparison)[output_columns]


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


def get_raw_eeud_demand():
    """Return raw EEUD-aligned 2023 demand values by sector and fuel."""
    tables = [
        get_raw_eeud_columns(pd.read_csv(path), sector_group)
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
    sector_group_emissions = pd.concat(rows, ignore_index=True)

    geothermal_fugitive = inventory[
        inventory["InventoryCode"] == GEOTHERMAL_FUGITIVE_CODE
    ][["Period", "HistoricalValue"]].copy()
    if not geothermal_fugitive.empty:
        geothermal_fugitive["SectorGroup"] = "Electricity generation"
        sector_group_emissions = pd.concat(
            [sector_group_emissions, geothermal_fugitive], ignore_index=True
        )
        fugitive_mask = sector_group_emissions["SectorGroup"] == "Fugitive emissions"
        sector_group_emissions.loc[
            fugitive_mask, "HistoricalValue"
        ] = sector_group_emissions.loc[
            fugitive_mask, "HistoricalValue"
        ] - sector_group_emissions.loc[
            fugitive_mask, "Period"
        ].map(
            geothermal_fugitive.set_index("Period")["HistoricalValue"]
        ).fillna(
            0
        )

    return (
        sector_group_emissions.groupby(["SectorGroup", "Period"], as_index=False)[
            "HistoricalValue"
        ]
        .sum()
        .sort_values(["SectorGroup", "Period"])
    )


def get_inventory_industry_emissions_by_fuel():
    """Return inventory industry emissions aggregated to fuel groups."""
    inventory = get_inventory_emissions()
    inventory = inventory[inventory["InventoryCode"].str.startswith("1.A.2", na=False)]
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
    return build_scenario_comparison(
        get_inventory_sector_group_emissions(),
        get_modelled_sector_group_emissions(),
        ["SectorGroup", "Period"],
        ["Scenario", "SectorGroup", "Period"],
        [
            "SectorGroup",
            "Scenario",
            "Period",
            "HistoricalValue",
            "ModelledValue",
            "Difference",
            "PercentDifference",
        ],
    )


def build_total_emissions_comparison():
    """Return total emissions comparison."""
    inventory_total = get_inventory_emissions()
    inventory_total = inventory_total[inventory_total["InventoryCode"] == "1. Energy"][
        ["Period", "HistoricalValue"]
    ].rename(columns={"HistoricalValue": "InventoryTotal"})
    modelled_total = (
        get_times_data("emissions.parquet")
        .groupby(["Scenario", "Period"], as_index=False)["Value"]
        .sum()
        .rename(columns={"Value": "ModelledValue"})
    )
    comparison = modelled_total.merge(inventory_total, on="Period", how="left").rename(
        columns={"InventoryTotal": "HistoricalValue"}
    )
    return calculate_differences(comparison)[
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
    return build_scenario_comparison(
        get_inventory_industry_emissions_by_fuel(),
        get_modelled_industry_emissions_by_fuel(),
        ["FuelGroup", "Period"],
        ["FuelGroup", "Scenario", "Period"],
        [
            "FuelGroup",
            "Scenario",
            "Period",
            "HistoricalValue",
            "ModelledValue",
            "Difference",
            "PercentDifference",
        ],
    )


def build_raw_eeud_demand_comparison():
    """Return raw EEUD demand compared with model demand by sector and fuel."""
    historical = cross_join_scenarios(
        get_raw_eeud_demand(),
        sorted(get_times_data("energy_demand.parquet")["Scenario"].unique()),
    )
    modelled = get_modelled_eeud_demand()
    comparison = historical.merge(
        modelled,
        on=["Scenario", "SectorGroup", "Sector", "Fuel", "Period"],
        how="outer",
    )
    comparison["HistoricalValue"] = comparison["HistoricalValue"].fillna(0)
    comparison["ModelledValue"] = comparison["ModelledValue"].fillna(0)
    comparison = calculate_differences(comparison)
    comparison["AbsoluteDifference"] = comparison["Difference"].abs()
    comparison = comparison[
        comparison["Difference"].round(DISPLAY_ZERO_DECIMALS) != 0
    ].copy()
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
    comparison = calculate_differences(comparison)
    comparison = comparison[
        comparison["Difference"].round(DISPLAY_ZERO_DECIMALS) != 0
    ].copy()
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


def get_historical_electricity(category, value_column, onsite_sector=None):
    """Load and standardise historical electricity data from the calibration CSV."""
    df = pd.read_csv(CALIBRATION_DATA / "electricity.csv")
    df = df[df["Category"] == category].copy()
    df = df.melt(
        id_vars=["Category", "sector", "Unit"],
        var_name="Period",
        value_name="HistoricalValue",
    )
    df["Period"] = pd.to_numeric(df["Period"], errors="coerce")
    df["HistoricalValue"] = pd.to_numeric(df["HistoricalValue"], errors="coerce")
    df = df.dropna(subset=["Period", "HistoricalValue"])

    if onsite_sector is not None:
        onsite = df[df["sector"] == "Unallocated onsite consumption"].copy()
        onsite["sector"] = onsite_sector
        df = pd.concat(
            [df[df["sector"] != "Unallocated onsite consumption"], onsite],
            ignore_index=True,
        )

    return (
        df.groupby(["sector", "Period", "Unit"], as_index=False)["HistoricalValue"]
        .sum()
        .rename(columns={"sector": value_column})
    )


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
    historical = get_historical_electricity(
        "Consumption", "Sector", onsite_sector="Industrial"
    )
    modelled = get_modelled_electricity_consumption()

    comparison = modelled[modelled["Period"].isin(historical["Period"].unique())].merge(
        historical[["Sector", "Period", "HistoricalValue"]],
        on=["Sector", "Period"],
        how="inner",
    )
    return calculate_differences(comparison)[
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


def build_total_electricity_consumption_comparison(electricity_consumption_comparison):
    """Return a total electricity consumption comparison table."""
    return build_total_comparison(
        electricity_consumption_comparison,
        [
            "Metric",
            "Scenario",
            "Period",
            "HistoricalValue",
            "ModelledValue",
            "Difference",
            "PercentDifference",
        ],
        "Total electricity consumption",
    ).sort_values(["Period", "Scenario"])


def build_electricity_generation_comparison():
    """Return the electricity generation calibration comparison table."""
    historical = get_historical_electricity("Net generation", "GenerationCategory")
    modelled = get_modelled_electricity_generation()
    modelled = modelled[modelled["Period"].isin(historical["Period"].unique())].copy()
    return build_scenario_comparison(
        historical,
        modelled,
        ["GenerationCategory", "Period"],
        ["Scenario", "GenerationCategory", "Period"],
        [
            "GenerationCategory",
            "Scenario",
            "Period",
            "HistoricalValue",
            "ModelledValue",
            "Difference",
            "PercentDifference",
        ],
    )


def build_total_generation_comparison(electricity_generation_comparison):
    """Return a total electricity generation comparison table."""
    return build_total_comparison(
        electricity_generation_comparison,
        [
            "Metric",
            "Scenario",
            "Period",
            "HistoricalValue",
            "ModelledValue",
            "Difference",
            "PercentDifference",
        ],
        "Total generation",
    ).sort_values(["Period", "Scenario"])


def format_table(df):
    """Format numeric columns for console-friendly table output."""
    out = df.copy()
    for col in FORMAT_COLUMNS:
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
    raw_eeud_demand_comparison = build_raw_eeud_demand_comparison()
    electricity_consumption_comparison = build_electricity_consumption_comparison()
    electricity_generation_comparison = build_electricity_generation_comparison()
    sections = [
        ("Emissions by sector group", build_emissions_comparison()),
        (
            "Industry emissions by fuel",
            build_industry_emissions_by_fuel_comparison(),
        ),
        (
            "Raw EEUD demand by sector and fuel",
            raw_eeud_demand_comparison,
        ),
        (
            "Raw EEUD demand by sector",
            build_raw_eeud_sector_total_comparison(raw_eeud_demand_comparison),
        ),
        ("Total emissions", build_total_emissions_comparison()),
        ("Electricity consumption", electricity_consumption_comparison),
        (
            "Total electricity consumption",
            build_total_electricity_consumption_comparison(
                electricity_consumption_comparison
            ),
        ),
        ("Electricity generation", electricity_generation_comparison),
        (
            "Total generation",
            build_total_generation_comparison(electricity_generation_comparison),
        ),
    ]

    markdown_parts = ["# Calibration Results", ""]
    for title, dataframe in sections:
        markdown_parts.append(f"## {title}")
        markdown_parts.append("")
        markdown_parts.append(
            dataframe_to_markdown(format_table(filter_assessment_years(dataframe)))
        )

    CALIBRATION_RESULTS_FILE.write_text(
        "\n".join(markdown_parts).strip() + "\n",
        encoding="utf-8",
    )
    print(f"Calibration results written to {CALIBRATION_RESULTS_FILE}")


if __name__ == "__main__":
    main()
