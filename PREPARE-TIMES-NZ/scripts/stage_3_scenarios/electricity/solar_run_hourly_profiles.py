"""
Run PVWatts hourly solar profiles for the configured NIWA scenarios.
"""

from __future__ import annotations

import csv
import json
from typing import Any

import numpy as np
import pandas as pd
from prepare_times_nz.utilities.filepaths import ASSUMPTIONS, DATA_RAW, STAGE_3_DATA

# pylint: disable=wrong-import-order
from PySAM import Pvwattsv8

SOLAR_SCENARIOS_FILE = (
    ASSUMPTIONS / "electricity_generation/renewable_curves/SolarPvScenarios.csv"
)
TIME_OF_DAY_FILE = DATA_RAW / "user_config/settings/time_of_day_types.csv"

OUTPUT_ROOT = STAGE_3_DATA / "electricity/solar_af"
PREPARED_EPW_DIR = OUTPUT_ROOT / "prepared_epw"
HOURLY_DIR = OUTPUT_ROOT / "hourly"
METADATA_DIR = OUTPUT_ROOT / "metadata"

EXPECTED_PATTERN = "TMY_NZ_{zone}.epw"

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

WEEKDAY_NAME_TO_INDEX = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}


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
        time_index.append(
            (int(row[0]), int(row[1]), int(row[2]), int(row[3]), int(row[4]))
        )

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

    start_weekday = data_periods[4].strip()
    days_in_year = int(data_periods[6])
    if start_weekday not in WEEKDAY_NAME_TO_INDEX:
        raise ValueError(
            f"Unsupported EPW start weekday {start_weekday!r} in {epw_path}"
        )

    return {
        "calendar_label": data_periods[3].strip(),
        "start_weekday": start_weekday,
        "days_in_year": days_in_year,
    }


def resolve_representative_calendar_year(start_weekday: str, days_in_year: int) -> int:
    """
    Map the EPW synthetic calendar metadata to a concrete Gregorian year.
    """
    target_weekday = WEEKDAY_NAME_TO_INDEX[start_weekday]
    is_leap_year = days_in_year == 366

    for year in range(2000, 2400):
        jan_1 = pd.Timestamp(year=year, month=1, day=1)
        if jan_1.weekday() != target_weekday:
            continue
        if jan_1.is_leap_year != is_leap_year:
            continue
        return year

    raise ValueError(
        "Could not resolve a representative year for "
        f"start_weekday={start_weekday!r}, days_in_year={days_in_year}"
    )


def load_solar_scenarios() -> list[dict[str, Any]]:
    """
    Load and normalize the configured solar archetype parameters.
    """
    df = pd.read_csv(SOLAR_SCENARIOS_FILE)
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
    for zone in ZONE_ORDER:
        path = epw_dir / EXPECTED_PATTERN.format(zone=zone)
        if path.exists():
            discovered[zone] = path

    missing = [zone for zone in ZONE_ORDER if zone not in discovered]
    if missing:
        raise FileNotFoundError(f"Missing EPW files for zones: {', '.join(missing)}")

    return discovered


def convert_hour_to_timeofday(df: pd.DataFrame) -> pd.DataFrame:
    """
    Match the project time-of-day mapping used in extract_ea_data.py.
    """
    time_of_day_types = pd.read_csv(TIME_OF_DAY_FILE)
    hour_to_time = dict(
        zip(time_of_day_types["Hour"], time_of_day_types["Time_Of_Day"])
    )
    df["Time_Of_Day"] = df["Hour"].map(hour_to_time)
    df["Time_Of_Day"] = df["Time_Of_Day"].fillna("N")
    return df


def convert_date_to_daytype(
    df: pd.DataFrame, date_col: str = "Trading_Date"
) -> pd.DataFrame:
    """
    Match the project weekday/weekend mapping used in extract_ea_data.py.
    """
    df[date_col] = pd.to_datetime(df[date_col])
    weekday = df[date_col].dt.weekday
    df["Day_Type"] = np.select(
        [weekday.isin([5, 6]), weekday.isin([0, 1, 2, 3, 4])],
        ["WE-", "WK-"],
        default="ERROR",
    )
    return df


def convert_date_to_season(
    df: pd.DataFrame, date_col: str = "Trading_Date"
) -> pd.DataFrame:
    """
    Match the project season mapping used in extract_ea_data.py.
    """
    df[date_col] = pd.to_datetime(df[date_col])
    month = df[date_col].dt.month

    df["Season"] = np.select(
        [
            month.isin([12, 1, 2]),
            month.isin([3, 4, 5]),
            month.isin([6, 7, 8]),
            month.isin([9, 10, 11]),
        ],
        ["SUM-", "FAL-", "WIN-", "SPR-"],
        default="ERROR",
    )
    return df


def create_timeslices(df: pd.DataFrame, date_col: str = "Trading_Date") -> pd.DataFrame:
    """
    Create project-style timeslices using the same logic as extract_ea_data.py.
    """
    df = convert_hour_to_timeofday(df)
    df = convert_date_to_daytype(df, date_col)
    df = convert_date_to_season(df, date_col)
    df["TimeSlice"] = df["Season"] + df["Day_Type"] + df["Time_Of_Day"]
    df = df.drop(columns=["Season", "Day_Type", "Time_Of_Day"])
    return df


def build_time_index(epw_files):
    """
    Build the shared non-calendar hourly index.

    All NIWA files should agree on month/day/hour/minute ordering, even if the
    representative calendar year differs by zone.
    """
    canonical = None
    canonical_zone = None
    canonical_metadata = None
    for zone in ZONE_ORDER:
        index = [
            (month, day, hour, minute)
            for _, month, day, hour, minute in parse_epw_time_index(epw_files[zone])
        ]
        metadata = parse_epw_data_period_metadata(epw_files[zone])
        if canonical is None:
            canonical = index
            canonical_zone = zone
            canonical_metadata = metadata
        elif canonical != index:
            raise ValueError(f"Time index mismatch between {canonical_zone} and {zone}")
        elif metadata != canonical_metadata:
            raise ValueError(
                "DATA PERIODS metadata mismatch between "
                f"{canonical_zone} and {zone}: {canonical_metadata} != {metadata}"
            )

    representative_year = resolve_representative_calendar_year(
        start_weekday=canonical_metadata["start_weekday"],
        days_in_year=canonical_metadata["days_in_year"],
    )

    rows = []
    for hour_index, (month, day, hour, minute) in enumerate(canonical, start=1):
        trading_date = pd.Timestamp(
            year=representative_year,
            month=month,
            day=day,
        )
        rows.append(
            {
                "hour_of_year": hour_index,
                "Trading_Date": trading_date,
                "Year": representative_year,
                "Month": month,
                "Day": day,
                "EPWHour": hour,
                "Hour": (hour - 1) % 24,
                "Minute": minute,
            }
        )
    return pd.DataFrame(rows)


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
    long_df = create_timeslices(long_df, date_col="Trading_Date")
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
