"""Create island-level wind timeslice availability factors from historical EMI data."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

import polars as pl
from prepare_times_nz.utilities.filepaths import ANALYSIS, ASSUMPTIONS, STAGE_1_DATA
from prepare_times_nz.utilities.logger_setup import logger

CUSTOM_ELE_ASSUMPTIONS = ASSUMPTIONS / "electricity_generation"
OUTPUT_LOCATION = ANALYSIS / "results/wind_availability_factors"
SI_WIND_PLANTS = {"KaiweraDowns", "white_hill"}
DEFAULT_WIND_TECH_ASSUMPTIONS = {
    "WindOn": 0.38,
    "WindFixOff": 0.50,
    "WindFloatOff": 0.50,
}


def load_inputs(
    assumptions_dir: Path = CUSTOM_ELE_ASSUMPTIONS,
    emi_md_path: Path = STAGE_1_DATA / "electricity_authority/emi_md.parquet",
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Load fleet metadata and raw EMI market data inputs."""
    fleet_data = pl.read_csv(assumptions_dir / "GenerationFleet.csv")
    emi_md = pl.read_parquet(emi_md_path)
    return fleet_data, emi_md


def convert_hour_to_timeofday(df: pl.DataFrame, hour_col: str = "Hour") -> pl.DataFrame:
    """Map hour-of-day to TIMES day-part labels (P, D, N)."""
    return df.with_columns(
        pl.when(pl.col(hour_col) == 18)
        .then(pl.lit("P"))
        .when((pl.col(hour_col) >= 7) & (pl.col(hour_col) <= 17))
        .then(pl.lit("D"))
        .otherwise(pl.lit("N"))
        .alias("Time_Of_Day")
    )


def convert_date_to_daytype(
    df: pl.DataFrame, date_col: str = "Trading_Date"
) -> pl.DataFrame:
    """Map dates to TIMES weekday/weekend labels."""
    return df.with_columns(
        pl.when(pl.col(date_col).dt.weekday().is_in([6, 7]))
        .then(pl.lit("WE-"))
        .when(pl.col(date_col).dt.weekday().is_in([1, 2, 3, 4, 5]))
        .then(pl.lit("WK-"))
        .otherwise(pl.lit("ERROR"))
        .alias("Day_Type")
    )


def convert_date_to_season(
    df: pl.DataFrame, date_col: str = "Trading_Date"
) -> pl.DataFrame:
    """Map calendar month to TIMES season labels."""
    return (
        df.with_columns(pl.col(date_col).dt.month().alias("Month"))
        .with_columns(
            pl.when(pl.col("Month").is_in([12, 1, 2]))
            .then(pl.lit("SUM-"))
            .when(pl.col("Month").is_in([3, 4, 5]))
            .then(pl.lit("FAL-"))
            .when(pl.col("Month").is_in([6, 7, 8]))
            .then(pl.lit("WIN-"))
            .when(pl.col("Month").is_in([9, 10, 11]))
            .then(pl.lit("SPR-"))
            .otherwise(pl.lit("ERROR"))
            .alias("Season")
        )
        .drop("Month")
    )


def create_timeslices(df: pl.DataFrame) -> pl.DataFrame:
    """Create TIMES timeslice codes by combining season, day type, and day-part."""
    return (
        convert_date_to_season(convert_date_to_daytype(convert_hour_to_timeofday(df)))
        .with_columns(
            (pl.col("Season") + pl.col("Day_Type") + pl.col("Time_Of_Day")).alias(
                "Timeslice"
            )
        )
        .drop(["Season", "Day_Type", "Time_Of_Day"])
    )


def check_grain(df: pl.DataFrame, grain_variables: list[str]) -> None:
    """Warn if provided columns do not uniquely define dataframe grain."""
    grain_check = (
        df.group_by(grain_variables)
        .agg(pl.len().alias("count"))
        .filter(pl.col("count") > 1)
    )
    if grain_check.height > 0:
        logger.warning("Non-unique grain for %s", grain_variables)


def aggregate_emi_data(emi_md: pl.DataFrame) -> pl.DataFrame:
    """Aggregate EMI data to Trading_Date/Trading_Period/Gen_Code."""
    check_grain(
        emi_md, ["Trading_Date", "Trading_Period", "Gen_Code", "POC_Code", "Nwk_Code"]
    )
    return (
        emi_md.filter(pl.col("Value").is_not_null())
        .group_by(["Trading_Date", "Trading_Period", "Gen_Code"])
        .agg(pl.sum("Value").alias("Value"))
    )


def normalise_trading_date(
    df: pl.DataFrame, date_col: str = "Trading_Date"
) -> pl.DataFrame:
    """Ensure Trading_Date is a Polars Date type."""
    dtype = df.schema.get(date_col)
    if dtype == pl.Date:
        return df
    if dtype == pl.Datetime:
        return df.with_columns(pl.col(date_col).cast(pl.Date))
    return df.with_columns(
        pl.col(date_col).cast(pl.Utf8).str.strptime(pl.Date, "%Y-%m-%d", strict=False)
    )


def add_timeslices_to_emi(df: pl.DataFrame) -> pl.DataFrame:
    """Derive Hour and TIMES timeslice fields from EMI date/period columns."""
    df = normalise_trading_date(df)
    df = df.with_columns(
        pl.col("Trading_Period")
        .cast(pl.Utf8)
        .str.extract(r"(\d+)$", 1)
        .cast(pl.Int32, strict=False)
        .alias("Trading_Time")
    )
    df = df.with_columns(((pl.col("Trading_Time") - 1) * 30 // 60).alias("Hour"))
    return create_timeslices(df)


def add_metadata(emi_md_agg: pl.DataFrame, fleet_data: pl.DataFrame) -> pl.DataFrame:
    """Join fleet metadata onto aggregated EMI data and remove unmatched rows."""
    metadata = (
        fleet_data.select(["EMI_Name", "TechnologyCode", "FuelType", "CapacityMW"])
        .group_by(["EMI_Name", "TechnologyCode", "FuelType"])
        .agg(pl.sum("CapacityMW").alias("CapacityMW"))
    )

    emi = add_timeslices_to_emi(emi_md_agg).rename({"Gen_Code": "EMI_Name"})
    emi = emi.join(metadata, on="EMI_Name", how="left")
    return emi.filter(pl.col("CapacityMW").is_not_null())


def wind_capacity_factors(df: pl.DataFrame) -> pl.DataFrame:
    """Compute hourly wind generation and construct DateTime stamps."""
    return (
        df.filter(pl.col("FuelType") == "Wind")
        .group_by(["EMI_Name", "Trading_Date", "Hour", "Timeslice"])
        .agg([pl.sum("Value").alias("Value"), pl.max("CapacityMW").alias("CapacityMW")])
        .with_columns((pl.col("Value") / 1e3).alias("Value_MWh"))
        .filter(pl.col("Hour") < 24)
        .with_columns(
            pl.datetime(
                year=pl.col("Trading_Date").dt.year(),
                month=pl.col("Trading_Date").dt.month(),
                day=pl.col("Trading_Date").dt.day(),
                hour=pl.col("Hour"),
                minute=pl.lit(0),
                second=pl.lit(0),
            ).alias("DateTime")
        )
    )


def remove_partial_years(df: pl.DataFrame) -> pl.DataFrame:
    """Filter known partial/abnormal plant-year combinations from the dataset."""
    partial_year_dict = {
        "KaiweraDowns": [2024],
        "turitea": [2024],
        "waipipi": [2022, 2023, 2024],
        "west_wind": [2020, 2021, 2022],
        "white_hill": [2020, 2024],
    }

    df = df.with_columns(pl.col("DateTime").dt.year().alias("Year"))
    exprs = [
        (pl.col("EMI_Name") == plant) & pl.col("Year").is_in(valid_years)
        for plant, valid_years in partial_year_dict.items()
    ]
    combined_expr = exprs[0]
    for expr in exprs[1:]:
        combined_expr = combined_expr | expr

    valid_years = combined_expr | (
        ~pl.col("EMI_Name").is_in(list(partial_year_dict.keys()))
    )
    return df.filter(valid_years)


def _add_region(df: pl.DataFrame) -> pl.DataFrame:
    """Assign NI/SI region using the hardcoded SI plant list."""
    return df.with_columns(
        pl.when(pl.col("EMI_Name").is_in(list(SI_WIND_PLANTS)))
        .then(pl.lit("SI"))
        .otherwise(pl.lit("NI"))
        .alias("Region")
    )


def make_island_timeslice_output(df: pl.DataFrame) -> pl.DataFrame:
    """Aggregate wind output to region-timeslice CFs and weighted annual CFs."""
    by_region_hour = (
        _add_region(df)
        .group_by(["Region", "DateTime", "Hour", "Timeslice"])
        .agg(
            [
                pl.sum("CapacityMW").alias("CapacityMW"),
                pl.sum("Value_MWh").alias("Value_MWh"),
            ]
        )
    )

    ts_cf = (
        by_region_hour.group_by(["Region", "Timeslice"])
        .agg(
            [
                pl.mean("CapacityMW").alias("CapacityMW"),
                pl.mean("Value_MWh").alias("Average_MWh"),
            ]
        )
        .with_columns(
            (pl.col("Average_MWh") / pl.col("CapacityMW")).alias("Capacity_Factor")
        )
    )

    avg_cf = (
        by_region_hour.group_by(["Region"])
        .agg(
            [
                pl.mean("CapacityMW").alias("CapacityMW"),
                pl.mean("Value_MWh").alias("Average_MWh"),
            ]
        )
        .with_columns(
            (pl.col("Average_MWh") / pl.col("CapacityMW")).alias("Weighted_CF")
        )
        .select(["Region", "Weighted_CF"])
    )

    return ts_cf.join(avg_cf, on="Region", how="left")


def filter_to_ni_curves(df: pl.DataFrame) -> pl.DataFrame:
    """Keep only NI curves for downstream use."""
    # Keep NI only: SI curves are lower than they should be because plant count is low
    # and those plants are currently underperforming their expected specs.
    return df.filter(pl.col("Region") == "NI")


def generate_curve_outputs(
    df: pl.DataFrame,
    tech_assumptions: Mapping[str, float] | None = None,
) -> pl.DataFrame:
    """Scale NI timeslice CFs to tech targets and format as RenewableCurves rows."""
    required_cols = {"Timeslice", "Capacity_Factor", "Weighted_CF"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns for formatting: {sorted(missing)}")

    assumptions = dict(tech_assumptions or DEFAULT_WIND_TECH_ASSUMPTIONS)

    current_weighted_cf = float(df.select(pl.col("Weighted_CF").first()).item())
    if current_weighted_cf <= 0:
        raise ValueError("Current weighted CF must be > 0 to scale timeslice curves.")

    base = df.select(["Timeslice", "Capacity_Factor"]).rename(
        {"Timeslice": "TimeSlice", "Capacity_Factor": "NI"}
    )

    output_tables: list[pl.DataFrame] = []
    for tech_code, target_weighted_cf in assumptions.items():
        scale = target_weighted_cf / current_weighted_cf
        tech_df = (
            base.with_columns((pl.col("NI") * scale).clip(0.0, 1.0).alias("NI"))
            .with_columns(pl.col("NI").alias("SI"))
            .with_columns(pl.lit(tech_code).alias("TechCode"))
            .select(["TimeSlice", "TechCode", "NI", "SI"])
        )
        output_tables.append(tech_df)

    return pl.concat(output_tables)


def run_analysis() -> pl.DataFrame:
    """Run full wind-curve analysis and write island-level output CSV."""
    fleet_data, emi_md = load_inputs()

    emi_md_agg = aggregate_emi_data(emi_md)
    emi_with_meta = add_metadata(emi_md_agg, fleet_data)
    emi_wind = wind_capacity_factors(emi_with_meta)
    emi_wind = remove_partial_years(emi_wind)
    result = make_island_timeslice_output(emi_wind)
    result = filter_to_ni_curves(result)

    OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)
    result = result.sort(["Region", "Timeslice"])

    outputs = generate_curve_outputs(result, DEFAULT_WIND_TECH_ASSUMPTIONS)
    result.write_csv(OUTPUT_LOCATION / "emi_ts_cf_by_island.csv")
    outputs.write_csv(OUTPUT_LOCATION / "wind_af_assumptions.csv")

    return result


def main() -> None:
    """Script entrypoint."""
    run_analysis()


if __name__ == "__main__":
    main()
