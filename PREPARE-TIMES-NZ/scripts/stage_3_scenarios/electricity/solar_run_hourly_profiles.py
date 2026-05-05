"""
Run PVWatts hourly solar profiles for the configured NIWA scenarios.
"""

from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
from prepare_times_nz.stage_0.stage_0_settings import BASE_YEAR
from prepare_times_nz.utilities.filepaths import ASSUMPTIONS, STAGE_3_DATA
from prepare_times_nz.utilities.timeslices import create_timeslices

# pylint: disable=wrong-import-order
from PySAM import Pvwattsv8

SOLAR_SCENARIOS_FILE = (
    ASSUMPTIONS / "electricity_generation/renewable_curves/SolarPvScenarios.csv"
)
EXCLUDED_SOLAR_TECHS = {"SolarFixed"}
# note that these are techs where we have data but not any existing
# techs.
# We remove it so it doesn't build into wem_wcm and similar files from
# the renewable curves
# If we use this tech later just remove the filter and data ready to go

OUTPUT_ROOT = STAGE_3_DATA / "electricity/solar_af"
PREPARED_EPW_DIR = OUTPUT_ROOT / "prepared_epw"
HOURLY_DIR = OUTPUT_ROOT / "hourly"
METADATA_DIR = OUTPUT_ROOT / "metadata"

EPW_FILENAME_PATTERN = re.compile(r"^TMY3_NZ_(?P<zone>[A-Z]{2})\.epw$")

ZONE_CODE_TO_REGION = {
    "AK": "Auckland",
    "BP": "Bay of Plenty",
    "CC": "Christchurch",
    "DN": "Dunedin",
    "EC": "East Coast",
    "HN": "Hamilton",
    "IN": "Invercargill",
    "MW": "Manawatu",
    "NL": "Northland",
    "NM": "Nelson-Marlborough",
    "NP": "New Plymouth",
    "OC": "Central Otago",
    "QL": "Queenstown-Lakes",
    "RR": "Rotorua",
    "TP": "Taupo",
    "WC": "West Coast",
    "WI": "Wairarapa",
    "WN": "Wellington",
}

ZONE_CODE_TO_ISLAND = {
    "AK": "NI",
    "BP": "NI",
    "CC": "SI",
    "DN": "SI",
    "EC": "NI",
    "HN": "NI",
    "IN": "SI",
    "MW": "NI",
    "NL": "NI",
    "NM": "SI",
    "NP": "NI",
    "OC": "SI",
    "QL": "SI",
    "RR": "NI",
    "TP": "NI",
    "WC": "SI",
    "WI": "NI",
    "WN": "NI",
}

ZONE_ORDER = [
    "NL",
    "AK",
    "HN",
    "BP",
    "RR",
    "TP",
    "NP",
    "EC",
    "MW",
    "WI",
    "WN",
    "NM",
    "WC",
    "CC",
    "QL",
    "OC",
    "DN",
    "IN",
]

ARRAY_TYPE_MAP = {
    "fixed_open_rack": 0,
    "fixed_roof_mount": 1,
    "single_axis_tracking": 2,
    "single_axis_backtracking": 3,
    "two_axis_tracking": 4,
}

MODULE_TYPE_MAP = {
    "standard": 0,
    "premium": 1,
    "thin_film": 2,
}

EPW_STANDARD_TZ = timezone(timedelta(hours=12), name="NZST_FIXED")
NZ_WALLCLOCK_TZ = ZoneInfo("Pacific/Auckland")


def ensure_output_dir(path):
    """
    Create an output directory with predictable permissions.
    """
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(0o755)
    return path


def read_epw_rows(epw_path):
    """
    Read an EPW file using the encodings present in the NIWA datasets.
    """
    last_error = None
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            with epw_path.open("r", encoding=encoding, newline="") as handle:
                return list(csv.reader(handle))
        except UnicodeDecodeError as exc:
            last_error = exc

    if last_error is not None:
        raise last_error

    raise ValueError(f"Could not read EPW rows from {epw_path}")


def parse_epw_time_index(epw_path):
    """
    Read the year/month/day/hour/minute tuple for each EPW data row.
    """
    rows = read_epw_rows(epw_path)[8:]
    time_index = []
    for row_num, row in enumerate(rows, start=9):
        if len(row) < 5:
            raise ValueError(
                f"EPW data row {row_num} has fewer than 5 columns in {epw_path}"
            )
        hour = int(row[3])
        minute = int(row[4])
        if minute not in {0, 60}:
            raise ValueError(
                f"Unsupported EPW minute value {minute} at row {row_num} in {epw_path}. "
                "The workflow expects NIWA EPW minute values of 0 or 60."
            )
        if not 1 <= hour <= 24:
            raise ValueError(
                f"Unsupported EPW hour value {hour} at row {row_num} in {epw_path}. "
                "The workflow expects EPW-standard 01..24 hour fields."
            )

        time_index.append((int(row[0]), int(row[1]), int(row[2]), hour, minute))

    if len(time_index) != 8760:
        raise ValueError(
            f"Expected 8760 EPW rows in {epw_path}, found {len(time_index)}"
        )

    return time_index


def parse_epw_data_period_metadata(epw_path) -> dict[str, Any]:
    """
    Read the shared TMY calendar metadata from the EPW header.
    """
    rows = read_epw_rows(epw_path)
    if len(rows) < 8:
        raise ValueError(f"Expected at least 8 EPW header rows in {epw_path}")

    data_periods = rows[7]
    if len(data_periods) < 7 or data_periods[0] != "DATA PERIODS":
        raise ValueError(f"Malformed DATA PERIODS header row in {epw_path}")

    metadata = {
        "calendar_label": data_periods[3].strip(),
        "start_weekday": data_periods[4].strip(),
    }

    # NIWA EPW headers may use either a numeric day count in column 7 or
    # MBIE TMY3-style start/end dates in columns 6 and 7.
    try:
        metadata["days_in_year"] = int(data_periods[6])
    except ValueError:
        metadata["start_date"] = data_periods[5].strip()
        metadata["end_date"] = data_periods[6].strip()
        metadata["days_in_year"] = 365

    return metadata


def validate_base_year_calendar():
    """
    Fail loudly until leap-year handling is implemented for solar timeslices.
    """
    if pd.Timestamp(year=BASE_YEAR, month=1, day=1).is_leap_year:
        raise ValueError(
            "Solar availability-factor workflow currently assumes a 365-day "
            f"calendar, but BASE_YEAR {BASE_YEAR} is a leap year. Revisit leap-year "
            "handling before regenerating solar availability factors."
        )


def validate_epw_calendar_assumptions(epw_path):
    """
    Fail loudly if an EPW file implies leap-year calendar handling.
    """
    metadata = parse_epw_data_period_metadata(epw_path)
    if metadata["days_in_year"] != 365:
        raise ValueError(
            "Solar availability-factor workflow currently assumes a 365-day "
            f"calendar, but {epw_path.name} declares {metadata['days_in_year']} "
            "days in its DATA PERIODS header. Revisit leap-year handling before "
            "regenerating solar availability factors."
        )


def get_canonical_epw_index(epw_path):
    """
    Return the shared month/day/hour/minute sequence for one EPW file.
    """
    raw_index = parse_epw_time_index(epw_path)
    validate_epw_calendar_assumptions(epw_path)
    return [(month, day, hour, minute) for _, month, day, hour, minute in raw_index]


def convert_epw_standard_time_to_wallclock(month: int, day: int, hour: int) -> datetime:
    """
    Convert a fixed NZST EPW interval-start hour to NZ wall-clock time.
    """
    standard_time = datetime(
        BASE_YEAR,
        month,
        day,
        hour,
        tzinfo=EPW_STANDARD_TZ,
    )
    return standard_time.astimezone(NZ_WALLCLOCK_TZ)


def format_time_index_rows(canonical_index):
    """
    Build hourly rows using the configured model base year calendar.
    """
    rows = []
    for hour_index, (month, day, hour, minute) in enumerate(canonical_index, start=1):
        interval_start_hour = (hour - 1) % 24
        trading_date = pd.Timestamp(year=BASE_YEAR, month=month, day=day)
        wall_clock = convert_epw_standard_time_to_wallclock(
            month=month,
            day=day,
            hour=interval_start_hour,
        )
        rows.append(
            {
                "hour_of_year": hour_index,
                "Trading_Date": trading_date,
                "Year": BASE_YEAR,
                "Month": month,
                "Day": day,
                "EPWHour": hour,
                "Hour": interval_start_hour,
                "Minute": minute,
                "WallClock_DateTime": pd.Timestamp(wall_clock),
                "WallClock_Date": pd.Timestamp(wall_clock.date()),
                "WallClock_Year": wall_clock.year,
                "WallClock_Month": wall_clock.month,
                "WallClock_Day": wall_clock.day,
                "WallClock_Hour": wall_clock.hour,
                "WallClock_UtcOffsetHours": (
                    wall_clock.utcoffset().total_seconds() / 3600
                ),
            }
        )
    return rows


def load_solar_scenarios() -> list[dict[str, Any]]:
    """
    Load and normalize the configured solar archetype parameters.
    """
    df = pd.read_csv(SOLAR_SCENARIOS_FILE)
    df = df[~df["Tech_TIMES"].isin(EXCLUDED_SOLAR_TECHS)].copy()
    scenarios = []

    for row in df.to_dict(orient="records"):
        scenario = dict(row)
        scenario["ArrayTypeCode"] = ARRAY_TYPE_MAP[scenario["ArrayType"]]
        scenario["ModuleTypeCode"] = MODULE_TYPE_MAP[scenario["ModuleType"]]
        scenario["UseWeatherFileAlbedo"] = str(
            scenario["UseWeatherFileAlbedo"]
        ).lower() in {
            "1",
            "true",
            "yes",
        }
        scenarios.append(scenario)

    return scenarios


def discover_epw_files(epw_dir):
    """
    Find one prepared EPW file for each expected NIWA climate zone.
    """
    discovered = {}
    unexpected = []
    for path in sorted(epw_dir.glob("*.epw")):
        match = EPW_FILENAME_PATTERN.match(path.name)
        if not match:
            unexpected.append(path.name)
            continue

        zone = match.group("zone")
        if zone in discovered:
            raise ValueError(
                f"Duplicate EPW files found for zone {zone}: "
                f"{discovered[zone].name} and {path.name}"
            )
        discovered[zone] = path

    if unexpected:
        raise ValueError(
            "Unsupported EPW filenames in prepared bundle: " f"{', '.join(unexpected)}"
        )

    missing = [zone for zone in ZONE_ORDER if zone not in discovered]
    if missing:
        raise FileNotFoundError(f"Missing EPW files for zones: {', '.join(missing)}")

    return discovered


def build_time_index(epw_files):
    """
    Build the shared hourly index using the model base-year calendar.

    All NIWA files should agree on month/day/hour/minute ordering. The EPW row
    year and header calendar metadata are ignored for timeslice construction.
    """
    validate_base_year_calendar()

    canonical = None
    canonical_zone = None
    for zone in ZONE_ORDER:
        index = get_canonical_epw_index(epw_files[zone])
        if canonical is None:
            canonical = index
            canonical_zone = zone
        elif canonical != index:
            raise ValueError(f"Time index mismatch between {canonical_zone} and {zone}")

    return pd.DataFrame(format_time_index_rows(canonical))


def build_model(epw_path, scenario):
    """
    Build a PVWatts model for one scenario-zone pair.
    """
    model = Pvwattsv8.default("PVWattsNone")  # pylint: disable=c-extension-no-member
    model.SolarResource.solar_resource_file = str(epw_path.resolve())
    model.Lifetime.system_use_lifetime_output = 0

    model.SystemDesign.system_capacity = float(scenario["SystemCapacityKW"])
    model.SystemDesign.array_type = int(scenario["ArrayTypeCode"])
    model.SystemDesign.tilt = float(scenario["TiltDeg"])
    model.SystemDesign.azimuth = float(scenario["AzimuthDeg"])
    model.SystemDesign.module_type = int(scenario["ModuleTypeCode"])
    model.SystemDesign.dc_ac_ratio = float(scenario["DcAcRatio"])
    model.SystemDesign.inv_eff = float(scenario["InvEffPercent"])
    model.SystemDesign.losses = float(scenario["LossesPercent"])
    model.SystemDesign.bifaciality = float(scenario["Bifaciality"])
    model.SystemDesign.gcr = float(scenario["Gcr"])
    model.SystemDesign.en_snowloss = 0

    use_weather_file_albedo = 1.0 if scenario["UseWeatherFileAlbedo"] else 0.0
    model.SolarResource.use_wf_albedo = use_weather_file_albedo
    if not use_weather_file_albedo:
        albedo = float(scenario["Albedo"])
        model.SolarResource.albedo = tuple(albedo for _ in range(12))

    model.Shading.shading_en_azal = 0
    model.Shading.shading_en_diff = 0
    model.Shading.shading_en_mxh = 0
    model.Shading.shading_en_string_option = 0
    model.Shading.shading_en_timestep = 0

    return model


def _json_default(value: Any):
    """
    Convert pandas / numpy scalar values to plain Python types for JSON output.
    """
    if hasattr(value, "item"):
        return value.item()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def collect_zone_hourly_rows(scenario_name, zone, time_index, generation):
    """
    Collect long-format hourly rows for a single zone.
    """
    region = ZONE_CODE_TO_REGION[zone]
    island = ZONE_CODE_TO_ISLAND[zone]

    rows = []
    for time_row, generation_kw_per_kw in zip(
        time_index.itertuples(index=False), generation
    ):
        rows.append(
            {
                "Scenario": scenario_name,
                "Tech_TIMES": scenario_name,
                "ZoneCode": zone,
                "Region": region,
                "Island": island,
                "Trading_Date": time_row.Trading_Date,
                "Year": time_row.Year,
                "Month": time_row.Month,
                "Day": time_row.Day,
                "Hour": time_row.Hour,
                "EPWHour": time_row.EPWHour,
                "Minute": time_row.Minute,
                "WallClock_DateTime": time_row.WallClock_DateTime,
                "WallClock_Date": time_row.WallClock_Date,
                "WallClock_Year": time_row.WallClock_Year,
                "WallClock_Month": time_row.WallClock_Month,
                "WallClock_Day": time_row.WallClock_Day,
                "WallClock_Hour": time_row.WallClock_Hour,
                "WallClock_UtcOffsetHours": time_row.WallClock_UtcOffsetHours,
                "generation_kw_per_kw": generation_kw_per_kw,
            }
        )

    return rows


def run_scenario_hourly_profiles(scenario, epw_files, time_index):
    """
    Run one solar archetype across all NIWA zones.
    """
    scenario_name = scenario["Tech_TIMES"]
    wide = time_index.copy()
    long_rows = []
    zone_results = []

    for zone in ZONE_ORDER:
        region = ZONE_CODE_TO_REGION[zone]
        island = ZONE_CODE_TO_ISLAND[zone]
        model = build_model(epw_files[zone], scenario)
        model.execute()
        generation = [float(value) for value in model.Outputs.gen]

        if len(generation) != 8760:
            raise ValueError(
                f"Expected 8760 PVWatts outputs for {scenario_name}/{zone}, "
                f"got {len(generation)}"
            )

        wide[zone] = generation
        zone_results.append(
            {
                "Tech_TIMES": scenario_name,
                "ZoneCode": zone,
                "Region": region,
                "Island": island,
                "EPWFile": epw_files[zone].name,
                "AnnualEnergyKWhPerKWDC": float(sum(generation)),
                "CapacityFactorPercent": float(model.Outputs.capacity_factor),
                "KWhPerKW": float(model.Outputs.kwh_per_kw),
            }
        )
        long_rows.extend(
            collect_zone_hourly_rows(
                scenario_name=scenario_name,
                zone=zone,
                time_index=time_index,
                generation=generation,
            )
        )

    long_df = pd.DataFrame(long_rows)
    long_df = create_timeslices(
        long_df,
        date_col="WallClock_Date",
        hour_col="WallClock_Hour",
    )
    return wide, long_df, zone_results


def save_scenario_outputs(scenario_name, scenario, wide, long_df, zone_results):
    """
    Save scenario outputs and metadata.
    """
    wide_path = HOURLY_DIR / f"{scenario_name}_hourly_by_zone.csv"
    long_path = HOURLY_DIR / f"{scenario_name}_hourly_long.csv"
    metadata_path = METADATA_DIR / f"{scenario_name}_run_metadata.json"

    wide.to_csv(wide_path, index=False)
    long_df.to_csv(long_path, index=False)

    with metadata_path.open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "Tech_TIMES": scenario_name,
                "Settings": scenario,
                "ZoneResults": zone_results,
                "Outputs": {
                    "HourlyByZoneCsv": str(wide_path),
                    "HourlyLongCsv": str(long_path),
                },
            },
            handle,
            indent=2,
            default=_json_default,
        )


def run_hourly_profiles():
    """
    Run PVWatts across all configured solar archetypes and NIWA zones.
    """
    scenarios = load_solar_scenarios()
    epw_files = discover_epw_files(PREPARED_EPW_DIR)
    time_index = build_time_index(epw_files)

    ensure_output_dir(HOURLY_DIR)
    ensure_output_dir(METADATA_DIR)

    combined_rows = []
    metadata_rows = []

    for scenario in scenarios:
        scenario_name = scenario["Tech_TIMES"]
        wide, long_df, zone_results = run_scenario_hourly_profiles(
            scenario=scenario,
            epw_files=epw_files,
            time_index=time_index,
        )
        save_scenario_outputs(
            scenario_name=scenario_name,
            scenario=scenario,
            wide=wide,
            long_df=long_df,
            zone_results=zone_results,
        )
        combined_rows.append(long_df)
        metadata_rows.extend(zone_results)

    all_hourly = pd.concat(combined_rows, ignore_index=True)
    all_hourly.to_csv(HOURLY_DIR / "all_scenarios_hourly_long.csv", index=False)
    pd.DataFrame(metadata_rows).to_csv(
        METADATA_DIR / "all_scenarios_zone_summary.csv", index=False
    )


if __name__ == "__main__":
    run_hourly_profiles()
