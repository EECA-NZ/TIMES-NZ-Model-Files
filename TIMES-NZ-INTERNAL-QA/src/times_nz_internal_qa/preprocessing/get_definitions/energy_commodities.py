"""
Get definitions of energy commodities. Combine fuel and sector codes.
"""

import pandas as pd
from times_nz_internal_qa.utilities.filepaths import (
    COMMODITY_CONCORDANCES,
    CONCORDANCES,
)


def get_energy_commodities():
    """
    Get definitions of energy commodities. Combine fuel and sector codes.
    """

    fuel_codes = pd.read_csv(CONCORDANCES / "code_mapping/fuel_codes.csv")
    sector_codes = pd.read_csv(CONCORDANCES / "code_mapping/sector_codes.csv")

    # cross join every combination of sector x fuel to label as the fuel
    df = fuel_codes.merge(sector_codes, how="cross")
    df["CommodityCode"] = df["SectorCode"] + df["CommodityCode"]

    df = pd.concat([df, fuel_codes])
    df["CommodityGroup"] = "Energy"

    df = df[["CommodityCode", "Commodity"]].drop_duplicates()

    df = df.rename(columns={"CommodityCode": "Commodity", "Commodity": "Fuel"})

    #  add distribution commodities manually

    df_elc_dist = pd.DataFrame()

    df_elc_dist["Commodity"] = ["ELCDD", "ELCHV"]
    df_elc_dist["Fuel"] = ["Electricity", "Electricity"]

    df = pd.concat([df, df_elc_dist])

    df = df.sort_values("Commodity")

    return df


def main():
    """script entrypoint"""
    df = get_energy_commodities()
    df.to_csv(COMMODITY_CONCORDANCES / "energy.csv", index=False)


if __name__ == "__main__":
    main()
