"""Tests for agriculture demand projection helpers."""

import csv
from pathlib import Path

from openpyxl import Workbook
from prepare_times_nz.stage_3.demand_projections import agriculture

# pylint: disable= duplicate-code
ASSUMPTION_COLUMNS = [
    "SectorGroup",
    "Sector",
    "Scenario",
    "Method",
    "Workbook",
    "SheetName",
    "SourceCategory1",
    "SourceCategory2",
    "ConstantIndex",
    "Note",
]

WORKBOOK_NAME = "mfe/Detailed-results-for-ERP2-projection-scenarios.xlsx"
SECTOR_GROUP = "Agriculture, Forestry and Fishing"

TEST_ASSUMPTIONS = [
    {
        "SectorGroup": SECTOR_GROUP,
        "Sector": "Dairy Cattle Farming",
        "Scenario": "Traditional",
        "Method": "Workbook",
        "Workbook": WORKBOOK_NAME,
        "SheetName": "Baseline",
        "SourceCategory1": "",
        "SourceCategory2": "Total dairy cattle",
        "ConstantIndex": "",
        "Note": "",
    },
    {
        "SectorGroup": SECTOR_GROUP,
        "Sector": "Dairy Cattle Farming",
        "Scenario": "Transformation",
        "Method": "Workbook",
        "Workbook": WORKBOOK_NAME,
        "SheetName": "Baseline low",
        "SourceCategory1": "",
        "SourceCategory2": "Total dairy cattle",
        "ConstantIndex": "",
        "Note": "",
    },
    {
        "SectorGroup": SECTOR_GROUP,
        "Sector": "Livestock Farming",
        "Scenario": "Traditional",
        "Method": "Workbook",
        "Workbook": WORKBOOK_NAME,
        "SheetName": "Baseline",
        "SourceCategory1": "",
        "SourceCategory2": "Sheep and beef 'stock units'",
        "ConstantIndex": "",
        "Note": "",
    },
    {
        "SectorGroup": SECTOR_GROUP,
        "Sector": "Forestry and Logging",
        "Scenario": "Traditional",
        "Method": "Workbook",
        "Workbook": WORKBOOK_NAME,
        "SheetName": "Baseline",
        "SourceCategory1": "Forestry (million m3)",
        "SourceCategory2": "Harvested timber (TRV)",
        "ConstantIndex": "",
        "Note": "",
    },
    {
        "SectorGroup": SECTOR_GROUP,
        "Sector": "Indoor Cropping",
        "Scenario": "Traditional",
        "Method": "Workbook",
        "Workbook": WORKBOOK_NAME,
        "SheetName": "Baseline",
        "SourceCategory1": "",
        "SourceCategory2": "Horticulture",
        "ConstantIndex": "",
        "Note": "",
    },
    {
        "SectorGroup": SECTOR_GROUP,
        "Sector": "Fishing, Hunting and Trapping",
        "Scenario": "Traditional",
        "Method": "Constant",
        "Workbook": "",
        "SheetName": "",
        "SourceCategory1": "",
        "SourceCategory2": "",
        "ConstantIndex": 1,
        "Note": "",
    },
]


def make_test_erp_workbook(path: Path):
    """Create a minimal ERP-like workbook with scenario sheets and year columns."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Baseline"

    for sheet_name, dairy_2050, livestock_2050 in [
        ("Baseline", 70, 80),
        ("Baseline low", 60, 65),
    ]:
        ws = (
            wb[sheet_name]
            if sheet_name in wb.sheetnames
            else wb.create_sheet(sheet_name)
        )
        ws.append([None, None])
        ws.append(["Scenario", None])
        ws.append([sheet_name, None])
        ws.append([None, None])
        ws.append([None, None])
        ws.append([None, None, 2023, 2025, 2030, 2050])
        ws.append([None, "Total dairy cattle", 100, 90, 80, dairy_2050])
        ws.append([None, "Sheep and beef 'stock units'", 100, 95, 90, livestock_2050])
        ws.append(
            ["Forestry (million m3)", "Harvested timber (TRV)", 100, 110, 130, 160]
        )
        ws.append([None, "Horticulture", 100, 105, 110, 120])
        ws.append(["Other agriculture", "Total", 100, 102, 104, 106])

    wb.save(path)


def write_assumptions_csv(path: Path, rows):
    """Write the agriculture assumptions test file from structured rows."""
    with path.open("w", newline="", encoding="utf-8") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=ASSUMPTION_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def get_index(df, sector, scenario, year):
    """Return one compiled index value for the requested sector/scenario/year."""
    return df[
        (df["Sector"] == sector) & (df["Scenario"] == scenario) & (df["Year"] == year)
    ]["Index"].iloc[0]


def test_get_agriculture_growth_indices_reads_workbook_mappings(tmp_path):
    """Workbook-mapped and constant agriculture projections should compile correctly."""
    external_data_dir = tmp_path / "external_data"
    workbook_dir = external_data_dir / "mfe"
    workbook_dir.mkdir(parents=True)
    workbook_path = workbook_dir / "Detailed-results-for-ERP2-projection-scenarios.xlsx"
    make_test_erp_workbook(workbook_path)

    assumptions_path = tmp_path / "agriculture_demand_projections.csv"
    write_assumptions_csv(assumptions_path, TEST_ASSUMPTIONS)

    df = agriculture.get_agriculture_growth_indices(
        assumptions_path=assumptions_path,
        external_data_dir=external_data_dir,
    )

    assert get_index(df, "Dairy Cattle Farming", "Traditional", 2025) == 0.9
    assert get_index(df, "Dairy Cattle Farming", "Traditional", 2024) == 0.95
    assert get_index(df, "Dairy Cattle Farming", "Transformation", 2050) == 0.6
    assert get_index(df, "Livestock Farming", "Traditional", 2050) == 0.8
    assert get_index(df, "Indoor Cropping", "Traditional", 2050) == 1.2
    assert get_index(df, "Fishing, Hunting and Trapping", "Traditional", 2042) == 1.0
