"""Electricity generation analysis charts."""

import times_nz_internal_qa.analysis.get_data as chart_data
from times_nz_internal_qa.analysis.analysis_chart_helpers import (
    create_scenario_facet_chart,
    create_scenario_line_chart,
    eeca_colours,
    save_chart,
    standardise_chart_data,
)


def create_generation_line_chart():
    """Create total electricity generation comparison chart."""

    df = chart_data.get_elec_gen()
    df = standardise_chart_data(df)

    p = create_scenario_line_chart(df, "Electricity generation")

    save_chart(p, "elec_gen_line.png")


def create_generation_mix_chart():
    """Grouped area facet by scenario showing fuel mix."""

    # df = chart_data.get_elec_gen_fuel_use()
    df = chart_data.get_elec_gen(groupby_cols="TechnologyGroup")

    # custom colours!
    ele_colours = [
        eeca_colours["teal"],
        eeca_colours["navy"],
        eeca_colours["coral"],
        eeca_colours["forest"],
        eeca_colours["paleblue"],
        eeca_colours["navy"],
        eeca_colours["forest"],
    ]

    df = standardise_chart_data(df)

    p = create_scenario_facet_chart(
        df,
        chart_title="Electricity generation by technology",
        group_var="TechnologyGroup",
        palette=ele_colours,
    )
    save_chart(p, "elec_gen_by_tech.png")


def create_thermal_generation_charts():
    """Grouped area facet for thermal generation."""

    print("Hello please write me ")


def create_battery_flows():
    """Battery capacity by technology group."""

    print("Hello please write me ")


def main():
    """Write all electricity generation charts."""

    create_generation_line_chart()
    create_generation_mix_chart()
    create_thermal_generation_charts()
    create_battery_flows()


if __name__ == "__main__":
    main()
