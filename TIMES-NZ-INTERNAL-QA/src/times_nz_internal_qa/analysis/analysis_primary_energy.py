"""Primary energy analysis charts."""

import times_nz_internal_qa.analysis.get_data as chart_data
from times_nz_internal_qa.analysis.analysis_chart_helpers import (
    create_scenario_facet_chart,
    save_chart_and_data,
    standardise_chart_data,
)


def create_lng_and_natural_gas_supply_chart():
    """
    Area chart showing domestic natural gas supply and LNG imports from primary
    energy production data.
    """

    gas_df = chart_data.get_lng_and_natural_gas_supply()
    gas_df = standardise_chart_data(gas_df)

    p = create_scenario_facet_chart(
        gas_df,
        "LNG and natural gas supply",
        group_var="SupplySource",
    )

    save_chart_and_data(gas_df, p, "primary_energy_lng_natural_gas_supply.png")


def create_lng_natural_gas_and_biogas_supply_chart():
    """
    Area chart showing domestic natural gas, LNG imports, and biogas supply from
    primary energy production data.
    """

    gas_df = chart_data.get_lng_natural_gas_and_biogas_supply()
    gas_df = standardise_chart_data(gas_df)

    p = create_scenario_facet_chart(
        gas_df,
        "LNG, natural gas, and biogas supply",
        group_var="SupplySource",
    )

    save_chart_and_data(
        gas_df,
        p,
        "primary_energy_lng_natural_gas_biogas_supply.png",
    )


def create_biomass_and_biogas_supply_chart():
    """
    Area chart showing biomass and biogas supply from primary energy production
    data.
    """

    biomass_df = chart_data.get_biomass_and_biogas_supply()
    biomass_df = standardise_chart_data(biomass_df)

    p = create_scenario_facet_chart(
        biomass_df,
        "Biomass and biogas supply",
        group_var="SupplySource",
    )

    save_chart_and_data(
        biomass_df,
        p,
        "primary_energy_biomass_biogas_supply.png",
    )


def main():
    """Write all primary energy charts."""

    create_lng_and_natural_gas_supply_chart()
    create_lng_natural_gas_and_biogas_supply_chart()
    create_biomass_and_biogas_supply_chart()


if __name__ == "__main__":
    main()
