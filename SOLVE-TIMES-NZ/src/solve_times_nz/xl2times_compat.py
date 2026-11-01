"""Project-local compatibility wrapper for xl2times 0.3.0."""

# The wrapper deliberately patches xl2times' private transform hook and keeps
# its demand transformation structurally close to the upstream implementation.
# pylint: disable=protected-access,too-many-locals

import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd
from pandas import DataFrame
from xl2times import transforms, utils
from xl2times.__main__ import main as xl2times_main
from xl2times.datatypes import Tag, TimesModel

_generate_topology_dictionary = transforms.generate_topology_dictionary
_process_user_constraint_tables = transforms.process_user_constraint_tables
_complete_dictionary = transforms.complete_dictionary
_apply_final_fixup = transforms.apply_final_fixup
_setup_logger = utils.setup_logger

LEGACY_EOTIME = 2200


def _output_directory_from_args(arguments: list[str]) -> Path:
    """Return xl2times' requested output directory from command-line arguments."""
    for index, argument in enumerate(arguments):
        if argument == "--output_dir" and index + 1 < len(arguments):
            return Path(arguments[index + 1]).resolve()
        if argument.startswith("--output_dir="):
            return Path(argument.removeprefix("--output_dir=")).resolve()
    return (Path.cwd() / "output").resolve()


def _setup_logger_in_output_directory(
    level: int | None,
    log_name: str = utils.default_log_name,
    log_dir: str = ".",
) -> None:
    """Keep xl2times' log alongside its DD output rather than in the caller CWD."""
    del log_dir
    output_dir = _output_directory_from_args(sys.argv[1:])
    output_dir.mkdir(parents=True, exist_ok=True)
    _setup_logger(level, log_name=log_name, log_dir=str(output_dir))


def _convert_to_veda_precision(tables: dict[str, DataFrame]) -> dict[str, DataFrame]:
    """Format floating-point DD values with VEDA's observed 15-digit precision."""

    def convert(value: object) -> str:
        if isinstance(value, float):
            if value.is_integer():
                return str(int(value))
            return f"{value:.15g}"
        return str(value)

    for key, dataframe in tables.items():
        tables[key] = dataframe.map(convert)
    return tables


def _with_optional_descriptions(
    tables: dict[str, DataFrame], model: TimesModel
) -> dict[str, DataFrame]:
    """Allow process and commodity declarations to omit descriptions."""
    for dataframe in (model.processes, model.commodities):
        if "description" not in dataframe.columns:
            dataframe["description"] = pd.NA
    return _generate_topology_dictionary(tables, model)


def _project_demands_with_zero_continuation(
    tables: dict[str, DataFrame], base_year: int
) -> DataFrame:
    """Project demand while allowing only a zero-demand continuation."""
    if not all(
        tag in tables for tag in (Tag.drvr_allocation, Tag.drvr_table, Tag.series)
    ):
        transforms.logger.warning("Missing required tables for demand projection.")
        return pd.DataFrame()
    series = (
        tables[Tag.series][["series_name", "year", "value"]]
        .pivot(index="year", columns="series_name", values="value")
        .reset_index()
    )
    drivers = tables[Tag.drvr_table]
    index_cols = [
        column for column in drivers.columns if column not in {"driver", "value"}
    ]
    series = (
        drivers.pivot(index=index_cols, columns="driver", values="value")
        .reset_index()
        .merge(series, how="outer", on="year")
    )
    series = pd.melt(
        series, id_vars=index_cols, var_name="series_name", value_name="value"
    )
    allocation = pd.melt(
        tables[Tag.drvr_allocation][
            ["region", "commodity", "driver", "calibration", "sensitivity"]
        ],
        id_vars=["region", "commodity"],
        var_name="series_type",
        value_name="series_name",
    )
    series = (
        allocation.merge(series, how="left", on=["region", "series_name"])
        .dropna(subset=["value"], ignore_index=True)
        .drop(columns=["series_name"])
        .drop_duplicates(keep="last", ignore_index=True)
    )
    index_cols = [
        column for column in series.columns if column not in {"value", "series_type"}
    ]
    series = series.pivot(
        index=index_cols, columns="series_type", values="value"
    ).reset_index()
    series["year"] = series["year"].astype(int)
    previous = series.copy().rename(columns={"year": "year_t-1"})[
        ["region", "commodity", "year_t-1", "source_filename", "driver"]
    ]
    series["year_t-1"] = series["year"] - 1
    series = series.merge(
        previous,
        how="left",
        on=["region", "commodity", "year_t-1", "source_filename"],
        suffixes=("", "_t-1"),
    ).dropna(subset=["driver_t-1"], ignore_index=True)
    prior_zero = series["driver_t-1"].eq(0)
    current_zero = series["driver"].eq(0)
    restart = prior_zero & ~current_zero
    if restart.any():
        records = series.loc[
            restart,
            ["region", "commodity", "year", "source_filename", "driver", "driver_t-1"],
        ].to_dict(orient="records")
        raise ValueError(
            "Demand drivers cannot restart from zero; "
            "provide explicit demand projections for these rows: " + str(records)
        )
    ratio = series["driver"].mask(prior_zero & current_zero, 1) / series[
        "driver_t-1"
    ].mask(prior_zero & current_zero, 1)
    series["multiplier"] = series["calibration"] + series["sensitivity"] * (ratio - 1)
    series = series.drop(
        columns=["year_t-1", "driver", "driver_t-1", "calibration", "sensitivity"]
    )
    series["multiplier"] = series["multiplier"].astype(float)
    series["multiplier"] = (
        series[["region", "commodity", "source_filename", "multiplier"]]
        .groupby(["region", "commodity", "source_filename"])
        .cumprod()
    )
    series["submodule"] = "main"
    series["module_name"] = (
        series["source_filename"].str.upper().str.replace("ScenDem_", "", case=False)
    )
    fi_t = tables[Tag.fi_t]
    base = fi_t.loc[
        (fi_t["year"] == base_year) & (fi_t["attribute"] == "COM_PROJ"),
        ["region", "attribute", "commodity", "value"],
    ].drop_duplicates(keep="last", ignore_index=True)
    projected = series.merge(base, how="inner", on=["region", "commodity"])
    projected["value"] = projected["value"] * projected["multiplier"]
    return projected.drop(columns="multiplier")


def _expand_multi_region_user_constraints(config, tables, model):
    """Expand a generic UC_FLO over a declared multi-region UC set."""
    declared_regions: set[str] = set()
    for table in tables:
        if table.tag == Tag.uc_t:
            for set_name in {"R_E", "R_S"}.intersection(table.uc_sets):
                declared_regions.update(
                    region.strip().upper()
                    for region in table.uc_sets[set_name].split(",")
                    if region.strip() and region.strip().lower() != "allregions"
                )
    original_regions = model.internal_regions
    model.internal_regions = original_regions.union(declared_regions)
    try:
        processed = _process_user_constraint_tables(config, tables, model)
    finally:
        model.internal_regions = original_regions
    expanded = []
    for source_table, table in zip(tables, processed, strict=True):
        if table.tag != Tag.uc_t or "region" not in table.dataframe:
            expanded.append(table)
            continue
        dataframe = table.dataframe.copy()
        multi_region = dataframe["region"].str.contains(",", regex=False, na=False)
        if multi_region.any():
            dataframe.loc[multi_region, "region"] = dataframe.loc[
                multi_region, "region"
            ].str.split(",")
            dataframe = dataframe.explode("region", ignore_index=True)
            dataframe["region"] = dataframe["region"].str.strip()
        source_columns = {str(column).upper() for column in source_table.dataframe}
        region_values = [
            source_table.uc_sets[name]
            for name in {"R_E", "R_S"}.intersection(source_table.uc_sets)
        ]
        if "UC_FLO" in source_columns and len(region_values) == 1:
            regions = [
                region.strip().upper()
                for region in region_values[0].split(",")
                if region.strip()
            ]
            flow_rows = dataframe.loc[dataframe["attribute"].eq("UC_FLO")]
            if regions and regions != ["ALLREGIONS"] and not flow_rows.empty:
                replicas = [flow_rows.assign(region=region) for region in regions]
                dataframe = pd.concat(
                    [dataframe.loc[~dataframe["attribute"].eq("UC_FLO")], *replicas],
                    ignore_index=True,
                )
        expanded.append(replace(table, dataframe=dataframe))
    return expanded


def _export_implied_emission_topology(model: TimesModel) -> dict[str, DataFrame]:
    """Ensure implied environmental FLO_EMIS links reach the exported TOP set."""
    tables = _complete_dictionary(model)
    if model.implied_topology.empty:
        return tables
    implied = model.implied_topology[["region", "process", "commodity", "io"]]
    topology = tables.get("Topology")
    if topology is None:
        tables["Topology"] = implied.drop_duplicates(ignore_index=True)
    else:
        tables["Topology"] = pd.concat(
            [topology, implied], ignore_index=True
        ).drop_duplicates(subset=["region", "process", "commodity", "io"], keep="first")
    return tables


def _drop_generated_residuals_after_legacy_horizon(
    config, tables: dict[str, DataFrame], model: TimesModel
) -> dict[str, DataFrame]:
    """Match VEDA by excluding derived stock-expiry rows outside `EOTIME`.

    VEDA's legacy 2200 year domain cannot contain an implied ``PRC_RESID = 0``
    row after that year.  xl2times creates such rows during its final fix-up
    from a process's lifetime.  Retain all source rows and lifetimes, but omit
    only generated zero residual rows outside the legacy domain.
    """
    fixed = _apply_final_fixup(config, tables, model)
    dataframe = fixed[Tag.fi_t]
    years = pd.to_numeric(dataframe["year"], errors="coerce")
    generated = dataframe["source_filename"].isna()
    implied_residual = (
        dataframe["attribute"].eq("PRC_RESID")
        & dataframe["value"].eq(0)
        & years.gt(LEGACY_EOTIME)
        & generated
    )
    fixed[Tag.fi_t] = dataframe.loc[~implied_residual].copy()
    return fixed


def main() -> None:
    """Run xl2times with the TIMES-NZ compatibility hooks applied."""
    transforms.generate_topology_dictionary = _with_optional_descriptions
    transforms._project_demands = _project_demands_with_zero_continuation
    transforms.process_user_constraint_tables = _expand_multi_region_user_constraints
    transforms.complete_dictionary = _export_implied_emission_topology
    transforms.apply_final_fixup = _drop_generated_residuals_after_legacy_horizon
    transforms.convert_to_string = _convert_to_veda_precision
    utils.setup_logger = _setup_logger_in_output_directory
    xl2times_main()


if __name__ == "__main__":
    main()
