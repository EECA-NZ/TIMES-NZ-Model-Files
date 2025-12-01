"""
Creates very small files for different demand device discount rates
"""

import pandas as pd
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.filepaths import STAGE_4_DATA

# CONSTANTS
OUTPUT_LOCATION = STAGE_4_DATA / "scen_discount_rate"

# FUNCTIONS


def create_discount_rate_table(process_wildcard, rate, process_set="DMD"):
    """
    Creates table intended to be used as TFM_INS for a scenario file
    process_wildcare is the applicable processes

    Assumes demand devices (DMD) but could expand to ELE etc

    """

    df = pd.DataFrame(
        {
            "Attribute": ["NCAP_DRATE"],
            "Pset_PN": [process_wildcard],
            "Pset_Set": [process_set],
            "AllRegions": [rate],
        }
    )

    return df


def save_discount_rates(df, name, label):
    """
    _save_data wrapper
    """
    _save_data(df, name, label, filepath=OUTPUT_LOCATION)


def main():
    """
    Entry point. Applies assumptions from assumptions doc
    """

    trad_discount_rates = pd.concat(
        [
            # default
            create_discount_rate_table("*", 0.1),
            # electricity too
            create_discount_rate_table("*", 0.1, "ELC"),
            # public (schools/healthcare)
            create_discount_rate_table("C_EDU*, C_HLTH*", 0.08),
        ]
    )

    save_discount_rates(
        trad_discount_rates,
        "discount_rate_traditional.csv",
        "Traditional Discount Rates",
    )

    trans_discount_rates = pd.concat(
        [
            # default
            create_discount_rate_table("*", 0.08),
            # all green investments (electricity/biomass demand devices)
            create_discount_rate_table("*ELC* *WOD*", 0.05),
            # and all elec plants
            create_discount_rate_table("*", 0.05, "ELC"),
            # public (schools/healthcare)
            create_discount_rate_table("C_EDU*, C_HLTH*", 0.02),
        ]
    )

    save_discount_rates(
        trans_discount_rates,
        "discount_rate_transformation.csv",
        "Transformation Discount Rates",
    )


if __name__ == "__main__":
    main()
