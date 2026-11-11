"""Create the requested standalone national 2025 heating-demand delivery.

This is an analysis-only deliverable helper. It reads the sector modules'
aligned historical check outputs, rather than model-facing 2023 base-year
files, and does not participate in the preparation workflow or feed any model
input.

The delivery intentionally excludes Aluminium, Methanol and Urea; excludes
Office Blocks diesel; and applies the agreed 0.63 PJ Food and Beverage
reduction. These delivery-specific adjustments must not be interpreted as
changes to EEUD, aligned check data, base-year demand, or demand projections.
"""

from pathlib import Path

import pandas as pd
from plotnine import (
    aes,
    element_rect,
    element_text,
    facet_wrap,
    geom_col,
    ggplot,
    labs,
    scale_fill_manual,
    scale_x_discrete,
    theme,
    theme_minimal,
)

MODULE_ROOT = Path(__file__).resolve().parents[1]
STAGE_2_DATA = MODULE_ROOT / "data_intermediate/stage_2_baseyear_data"
OUTPUT_PATH = MODULE_ROOT / "analysis/results/historical_demand_2025.csv"
CHART_PATH = (
    MODULE_ROOT / "analysis/results/historical_demand_2025_by_sector_and_heat_band.png"
)
TOTALS_CHART_PATH = MODULE_ROOT / "analysis/results/historical_demand_2025_totals.png"
NOTES_PATH = MODULE_ROOT / "analysis/results/historical_demand_2025_notes.md"
YEAR = 2025
EXCLUDED_SECTORS = ["Aluminium", "Methanol", "Urea"]
EXCLUDED_SECTOR_FUELS = [("Office Blocks", "Diesel")]
CHART_EXCLUDED_SECTORS = ["Iron & Steel", "Mining", "Forestry and Logging"]
OTHER_CHART_FUELS = ["Biogas", "Diesel", "Fuel Oil", "LPG"]
DELIVERY_SECTOR_LABELS = {"WSR": "Warehousing and Retail"}
FOOD_AND_BEVERAGE_REDUCTION_PJ = 0.63
FUEL_COLOURS = {
    # TIMES-NZ-INTERNAL-QA analysis palette.
    "Natural Gas": "#5A1A5E",
    "Coal": "#2F2F2F",
    "Wood": "#41B496",
    "Electricity": "#4184A8",
    "LPG": "#C346CE",
    "Fuel Oil": "#E94E24",
    "Geothermal": "#ED6D63",
    "Biogas": "#ED6D63",
    "Diesel": "#5A1A5E",
    "Other": "#C346CE",
}

SOURCES = {
    "Industrial process heat": (
        STAGE_2_DATA / "industry/checks/times_eeud_alignment_timeseries.csv",
        lambda df: df["EndUse"].str.contains("Process Requirements", na=False),
    ),
    "Agriculture process heat and space heating": (
        STAGE_2_DATA
        / "ag_forest_fish/checks/1_sector_alignment/times_eeud_alignment_timeseries.csv",
        lambda df: df["EndUse"].str.contains(
            "Process Requirements|Space Heating", regex=True, na=False
        ),
    ),
    "Commercial space and water heating": (
        STAGE_2_DATA
        / "commercial/checks/1_sector_alignment/times_eeud_alignment_timeseries.csv",
        lambda df: df["EndUse"].str.contains(
            "Space Heating|Water Heating", regex=True, na=False
        ),
    ),
}


def load_requested_rows(label: str, path: Path, enduse_filter) -> pd.DataFrame:
    """Load one aligned 2025 sector extract and identify its requested scope."""
    df = pd.read_csv(path)
    required_columns = {"Year", "EndUse", "Fuel", "Value", "Unit"}
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"{path} is missing required columns: {sorted(missing)}")

    out = df.loc[(df["Year"] == YEAR) & enduse_filter(df)].copy()
    if out.empty:
        raise ValueError(f"No {YEAR} rows selected from {path}")
    if set(out["Unit"].dropna()) != {"PJ"}:
        raise ValueError(f"Expected PJ units in {path}")

    out.insert(0, "Extract", label)
    return out


def apply_delivery_adjustments(output: pd.DataFrame) -> pd.DataFrame:
    """Apply agreed removals and Food and Beverage reduction to the delivery."""
    adjusted = output.loc[~output["Sector"].isin(EXCLUDED_SECTORS)].copy()
    for sector, fuel in EXCLUDED_SECTOR_FUELS:
        excluded = (adjusted["Sector"] == sector) & (adjusted["Fuel"] == fuel)
        if not excluded.any():
            raise ValueError(f"No {fuel} rows found for {sector}")
        adjusted = adjusted.loc[~excluded].copy()
    food_and_beverage = adjusted["Sector"] == "Food and Beverage"
    food_and_beverage_total = adjusted.loc[food_and_beverage, "Value"].sum()
    if food_and_beverage_total <= FOOD_AND_BEVERAGE_REDUCTION_PJ:
        raise ValueError("Food and Beverage adjustment would make demand negative")
    # shortcut: agreed delivery adjustment, replace when the source data is corrected.
    adjusted.loc[food_and_beverage, "Value"] *= (
        food_and_beverage_total - FOOD_AND_BEVERAGE_REDUCTION_PJ
    ) / food_and_beverage_total
    adjusted["Sector"] = adjusted["Sector"].replace(DELIVERY_SECTOR_LABELS)
    return adjusted


def write_delivery_note() -> None:
    """Record the delivery scope and adjustments beside the generated files."""
    NOTES_PATH.write_text(
        "# 2025 historical demand extract\n\n"
        "Values are national PJ demand selected from the 2025 sector-alignment "
        "outputs.\n\n"
        "## Delivery adjustments\n\n"
        "- Aluminium, Methanol and Urea are excluded.\n"
        "- Food and Beverage is reduced by 0.63 PJ proportionally across its "
        "existing rows.\n"
        "- Office Blocks diesel is excluded. It is likely misallocated by EEUD and "
        "should be corrected in TIMES preparation rather than treated as valid "
        "commercial heating demand.\n"
        "- WSR is labelled Warehousing and Retail for this delivery.\n"
    )


def prepare_chart_data(output: pd.DataFrame) -> pd.DataFrame:
    """Add chart-only fuel and heat-band categories."""
    chart_data = output.copy()
    chart_data["ChartFuel"] = chart_data["Fuel"].where(
        ~chart_data["Fuel"].isin(OTHER_CHART_FUELS), "Other"
    )
    chart_data["HeatBand"] = ""
    chart_data.loc[
        chart_data["EndUse"].str.contains("Low Temperature", na=False), "HeatBand"
    ] = "Low temperature"
    chart_data.loc[
        chart_data["EndUse"].str.contains(
            "Intermediate Heat|Cooking", regex=True, na=False
        ),
        "HeatBand",
    ] = "Intermediate temperature"
    chart_data.loc[
        chart_data["EndUse"].str.contains("High Temperature", na=False), "HeatBand"
    ] = "High temperature"
    if (chart_data["HeatBand"] == "").any():
        raise ValueError("Historical demand contains an unrecognised heat band")
    return chart_data


def make_sector_heat_band_chart(output: pd.DataFrame) -> None:
    """Save 2025 heating demand by sector, simplified heat band, and fuel."""
    chart_data = prepare_chart_data(
        output.loc[~output["Sector"].isin(CHART_EXCLUDED_SECTORS)]
    )
    chart_data = chart_data.groupby(
        ["Sector", "HeatBand", "ChartFuel"], as_index=False
    )["Value"].sum()
    chart_data["HeatBand"] = pd.Categorical(
        chart_data["HeatBand"],
        categories=[
            "Low temperature",
            "Intermediate temperature",
            "High temperature",
        ],
        ordered=True,
    )
    sector_order = (
        chart_data.groupby("Sector", observed=True)["Value"]
        .sum()
        .sort_values(ascending=False)
        .index
    )
    chart_data["Sector"] = pd.Categorical(
        chart_data["Sector"], categories=sector_order, ordered=True
    )

    chart = (
        ggplot(chart_data, aes(x="HeatBand", y="Value", fill="ChartFuel"))
        + geom_col()
        + facet_wrap("~Sector", ncol=3)
        + scale_x_discrete(
            labels={
                "Low temperature": "Low temp\n(<100 °C)",
                "Intermediate temperature": "Intermediate\n(100–300 °C)",
                "High temperature": "High temp\n(>300 °C)",
            }
        )
        + scale_fill_manual(values=FUEL_COLOURS)
        + labs(
            title="2025 heating demand: key sectors",
            x="Temperature band",
            y="PJ",
            fill="Fuel",
            caption="Other = Biogas, Diesel, Fuel Oil and LPG. Excludes residential",
        )
        + theme_minimal()
        + theme(
            axis_text_x=element_text(),
            legend_position="bottom",
            panel_border=element_rect(color="#6c757d", fill=None, size=0.8),
            strip_background=element_rect(fill="#e9ecef", color="#6c757d", size=0.8),
            strip_text=element_text(weight="bold"),
        )
    )
    chart.save(CHART_PATH, dpi=300, height=14, width=14)


def make_totals_chart(output: pd.DataFrame) -> None:
    """Save total 2025 heating demand by simplified heat band and fuel."""
    chart_data = prepare_chart_data(output)
    chart_data = chart_data.groupby(["HeatBand", "ChartFuel"], as_index=False)[
        "Value"
    ].sum()
    chart_data["HeatBand"] = pd.Categorical(
        chart_data["HeatBand"],
        categories=[
            "Low temperature",
            "Intermediate temperature",
            "High temperature",
        ],
        ordered=True,
    )

    chart = (
        ggplot(chart_data, aes(x="HeatBand", y="Value", fill="ChartFuel"))
        + geom_col()
        + scale_x_discrete(
            labels={
                "Low temperature": "Low temp\n(<100 °C)",
                "Intermediate temperature": "Intermediate\n(100–300 °C)",
                "High temperature": "High temp\n(>300 °C)",
            }
        )
        + scale_fill_manual(values=FUEL_COLOURS)
        + labs(
            title="2025 heating demand",
            subtitle="Selected sectors",
            x="Temperature band",
            y="PJ",
            fill="Fuel",
            caption="Excludes residential, Tiwai, Ballance, Methanex, and Wattie's-Heinz",
        )
        + theme_minimal()
        + theme(legend_position="bottom")
    )
    chart.save(TOTALS_CHART_PATH, dpi=300, height=7, width=8)


def main() -> None:
    extracts = [
        load_requested_rows(label, path, enduse_filter)
        for label, (path, enduse_filter) in SOURCES.items()
    ]
    output = pd.concat(extracts, ignore_index=True, sort=False)
    output = apply_delivery_adjustments(output)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(OUTPUT_PATH, index=False)
    write_delivery_note()
    make_sector_heat_band_chart(output)
    make_totals_chart(output)

    print(f"Wrote {len(output):,} rows to {OUTPUT_PATH}")
    print(f"Wrote chart to {CHART_PATH}")
    print(f"Wrote totals chart to {TOTALS_CHART_PATH}")
    print(f"Wrote notes to {NOTES_PATH}")
    print(output.groupby("Extract")["Value"].sum().round(3).to_string())


if __name__ == "__main__":
    main()
