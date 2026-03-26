"""Tests for solar-script timeslice helpers."""

import importlib.util
from pathlib import Path

import pandas as pd


def load_solar_run_hourly_profiles():
    """
    Load the script module directly from its path for test usage.
    """
    module_path = (
        Path(__file__).resolve().parents[1]
        / "scripts/stage_3_scenarios/electricity/solar_run_hourly_profiles.py"
    )
    spec = importlib.util.spec_from_file_location(
        "solar_run_hourly_profiles", module_path
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_create_timeslices_uses_project_time_of_day_and_daytype_definitions():
    """
    Shared timeslice construction should match the active repo settings.
    """
    module = load_solar_run_hourly_profiles()
    df = pd.DataFrame(
        {
            "Trading_Date": pd.to_datetime(
                ["2023-01-02", "2023-01-07", "2023-07-03", "2023-09-10"]
            ),
            "Hour": [18, 18, 7, 19],
        }
    )

    result = module.create_timeslices(df)

    assert result["TimeSlice"].tolist() == [
        "SUM-WK-P",
        "SUM-WE-P",
        "WIN-WK-D",
        "SPR-WE-N",
    ]


def test_build_time_index_uses_model_base_year_and_ignores_epw_calendar_metadata(
    tmp_path,
):
    """
    Solar timeslices should use the model base year rather than the EPW calendar.
    """
    module = load_solar_run_hourly_profiles()

    def make_epw(path: Path, header_year: int):
        header = [
            [
                "LOCATION",
                "Test",
                "Test",
                "New Zealand",
                "TMY2",
                "0",
                "0",
                "0",
                "0",
                "0",
            ],
            ["DESIGN CONDITIONS", "0"],
            ["TYPICAL/EXTREME PERIODS", "0"],
            ["GROUND TEMPERATURES", "0"],
            ["HOLIDAYS/DAYLIGHT SAVING", "No", "0", "0", "0"],
            ["COMMENTS 1", "Synthetic test EPW"],
            ["COMMENTS 2", "Synthetic test EPW"],
            ["DATA PERIODS", "1", "1", "TMY2 Year", "Monday", "1", "365"],
        ]
        rows = []
        for day in pd.date_range(
            f"{header_year}-01-01", f"{header_year}-12-31", freq="D"
        ):
            for hour in range(1, 25):
                rows.append(
                    [
                        f"{day.year:04d}",
                        f"{day.month:02d}",
                        f"{day.day:02d}",
                        f"{hour:02d}",
                        "60",
                    ]
                )

        with path.open("w", encoding="utf-8", newline="") as handle:
            for row in header + rows:
                handle.write(",".join(row) + "\n")

    epw_files = {}
    for zone in module.ZONE_ORDER:
        path = tmp_path / f"TMY_NZ_{zone}.epw"
        make_epw(path, 1999 if zone == "AK" else 2007)
        epw_files[zone] = path

    time_index = module.build_time_index(epw_files)

    assert time_index["Trading_Date"].min() == pd.Timestamp("2023-01-01")
    assert time_index["Trading_Date"].max() == pd.Timestamp("2023-12-31")
    assert time_index.iloc[0]["Trading_Date"].day_name() == "Sunday"


def test_build_time_index_rejects_leap_base_year(tmp_path):
    """
    Leap-year base calendars should fail until the workflow handles them explicitly.
    """
    module = load_solar_run_hourly_profiles()

    def make_epw(path: Path):
        header = [
            [
                "LOCATION",
                "Test",
                "Test",
                "New Zealand",
                "TMY2",
                "0",
                "0",
                "0",
                "0",
                "0",
            ],
            ["DESIGN CONDITIONS", "0"],
            ["TYPICAL/EXTREME PERIODS", "0"],
            ["GROUND TEMPERATURES", "0"],
            ["HOLIDAYS/DAYLIGHT SAVING", "No", "0", "0", "0"],
            ["COMMENTS 1", "Synthetic test EPW"],
            ["COMMENTS 2", "Synthetic test EPW"],
            ["DATA PERIODS", "1", "1", "TMY2 Year", "Sunday", "1", "365"],
        ]
        rows = []
        for day in pd.date_range("2007-01-01", "2007-12-31", freq="D"):
            for hour in range(1, 25):
                rows.append(
                    [
                        f"{day.year:04d}",
                        f"{day.month:02d}",
                        f"{day.day:02d}",
                        f"{hour:02d}",
                        "60",
                    ]
                )

        with path.open("w", encoding="utf-8", newline="") as handle:
            for row in header + rows:
                handle.write(",".join(row) + "\n")

    epw_files = {}
    for zone in module.ZONE_ORDER:
        path = tmp_path / f"TMY_NZ_{zone}.epw"
        make_epw(path)
        epw_files[zone] = path

    original_base_year = module.BASE_YEAR
    module.BASE_YEAR = 2024
    try:
        try:
            module.build_time_index(epw_files)
            raise AssertionError("Expected leap-year base-year guard to raise")
        except ValueError as exc:
            assert "BASE_YEAR 2024 is a leap year" in str(exc)
    finally:
        module.BASE_YEAR = original_base_year
