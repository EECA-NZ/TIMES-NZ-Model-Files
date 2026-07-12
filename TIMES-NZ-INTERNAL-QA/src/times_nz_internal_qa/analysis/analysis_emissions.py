"""Emissions analysis charts."""

import numpy as np
import times_nz_internal_qa.analysis.get_data as chart_data
from times_nz_internal_qa.analysis.analysis_chart_helpers import (
    create_scenario_facet_chart,
    create_scenario_line_chart,
    save_chart_and_data,
    standardise_chart_data,
)


def create_emissions_line(comparison=False):
    """Create emissions line chart, optionally with other-model comparisons."""

    emissions_df = chart_data.get_emissions(compare_other_models=comparison)

    emissions_df = emissions_df[emissions_df["Scenario"] != "ERP2"]
    emissions_df = standardise_chart_data(emissions_df)

    chart_title = "Energy emissions"
    filename = "emissions_line"

    if comparison:
        chart_title = "Energy emissions comparison"
        filename = "emissions_line_comparison"

    p = create_scenario_line_chart(emissions_df, chart_title)
    save_chart_and_data(emissions_df, p, filename)


def create_emissions_breakdown():
    """Create area facet chart for emissions share by sector."""

    emissions_df = chart_data.get_emissions_by_sector_group()

    key_sectors = ["Electricity generation", "Industry", "Transport"]
    grain_vars = [
        "Scenario",
        "Period",
        "Unit",
        "SectorGroup",
    ]

    emissions_df["SectorGroup"] = np.where(
        emissions_df["SectorGroup"].isin(key_sectors),
        emissions_df["SectorGroup"],
        "Other",
    )

    emissions_df = emissions_df.groupby(grain_vars)["Value"].sum().reset_index()
    emissions_df = standardise_chart_data(emissions_df)

    p = create_scenario_facet_chart(emissions_df, "Emissions by sector", "SectorGroup")
    save_chart_and_data(emissions_df, p, "emissions_sector_facet.png")


def main():
    """Write all emissions charts."""

    create_emissions_line()
    # create_emissions_line(comparison=True)
    create_emissions_breakdown()


if __name__ == "__main__":
    main()
