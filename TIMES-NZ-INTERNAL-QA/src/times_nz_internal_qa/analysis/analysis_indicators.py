"""Indicator analysis charts."""

import times_nz_internal_qa.analysis.get_data as chart_data
from times_nz_internal_qa.analysis.analysis_chart_helpers import (
    create_scenario_line_chart,
    save_chart,
)


def create_ren_tfec_chart():
    """Create renewable share of TFEC line chart."""

    tfec_df = chart_data.get_renewable_tfec()
    tfec_df["Value"] = tfec_df["RenewableShareOfTFEC"] * 100
    tfec_df["Unit"] = "%"

    p = create_scenario_line_chart(tfec_df, "Renewable share of TFEC")
    save_chart(p, "indicator_ren_tfec.png")


def create_ren_gen_chart():
    """Create renewable share of electricity generation line chart."""

    ren_elec = chart_data.get_renewable_electricity_share()
    ren_elec["Value"] = ren_elec["RenewableShareOfElectricity"] * 100
    ren_elec["Unit"] = "%"

    p = create_scenario_line_chart(
        ren_elec, "Renewable share of electricity generation", yaxis_0=False
    )
    save_chart(p, "indicator_ren_gen.png")


def main():
    """Write all indicator charts."""

    create_ren_gen_chart()
    create_ren_tfec_chart()


if __name__ == "__main__":
    main()
