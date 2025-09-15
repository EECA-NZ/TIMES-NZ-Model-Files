"""
This module loads our processed oil and gas data and creates three outputs:

1) gas_supply processes (declarations of the processes and some stats about em)
2)


"""

import numpy as np
import pandas as pd
from prepare_times_nz.utilities.filepaths import (
    ASSUMPTIONS,
    CONCORDANCES,
    STAGE_3_DATA,
    STAGE_4_DATA,
)

USD_TO_NZD = 1.68
LITRES_PER_BARREL = 158.987

OG_ASSUMPTIONS = ASSUMPTIONS / "oil_and_gas/"
# identify required input files

price_assumptions = OG_ASSUMPTIONS / "commodity_prices.csv"
fuel_properties = OG_ASSUMPTIONS / "fuel_properties.csv"
fug_emissions = OG_ASSUMPTIONS / "fugitive_emission_factors.csv"
gas_file = STAGE_3_DATA / "oil_and_gas/oil_and_gas_projections.csv"
fuel_codes = CONCORDANCES / "oil_and_gas/fuel_codes.csv"


OUTPUT_LOCATION = STAGE_4_DATA / "base_year_pri"


# identify field name mapped to TIMES
FIELD_MAPPING = {"Kapuni": "MINNGA-KAP"}


def aggregate_fields(df, field_mapping, default="MINNGA-OTH"):
    """
    The input dataframe fields are aggregated for TIMES
    It's either Kapuni, or everyone else
    We then aggregate values together
    """

    df["TechName"] = df["Field"].map(field_mapping).fillna(default)
    cols = [col for col in df.columns if col not in ["Value", "Field"]]
    df = df.groupby(cols)["Value"].sum().reset_index()

    return df


def get_veda_deliverability(df, resource_types):
    """aggregates total deliverability as needed based on the resource types
    Then reshapes to Veda taggable table"""

    # take the resource options you want
    df = df[df["ResourceType"].isin(resource_types)]
    # add together per field/year as needed
    df = df.groupby(["TechName", "Year"])["Value"].sum().reset_index()

    # reshape
    df["Attribute"] = "ACT_BND"
    df["Region"] = "NI"

    return df


def get_natural_gas_price_forecasts():
    """Read the commodity price assumptions
    Filter for NGA
    Reshape for Veda
    NOTE: doesn't distinguish by field - we cross join these to all our fields
    """
    df = pd.read_csv(price_assumptions)
    conc = pd.read_csv(fuel_codes)
    df = df.merge(conc, on="Fuel", how="left")
    df = df[df["Fuel_TIMES"] == "NGA"]
    # ALERT: INPUTS ARE NZD/GJ ALREADY

    df = df[["Year", "Value"]]

    df["Year"] = "Cost~" + df["Year"].astype(str)

    df = df.pivot_table(index=None, columns="Year", values="Value")

    return df


def get_natural_gas_fugitive_emissions():
    """Read the emissions factors assumptions
    Aggregate by TIMES field
    Reshape for Veda"""
    df = pd.read_csv(fug_emissions)
    df = df.groupby(["TIMES_Field"])["Emissions_Factor"].sum().reset_index()
    df = df.rename(
        columns={"TIMES_Field": "TechName", "Emissions_Factor": "ENV_ACT~GASCO2"}
    )
    return df


def get_nga_costs_emissions():
    """Combines the costs and emissions data for a single table
    Uses the field codes listed in the emissions file
    and attaches costs to all of these"""
    costs = get_natural_gas_price_forecasts()
    efs = get_natural_gas_fugitive_emissions()

    df = efs.merge(costs, how="cross")
    return df


def get_fuel_gj_per_barrel():
    """Reads fuel properties assumptions and calcs gj per barrel
    Requires LITRES_PER_BARREL constant

    """

    properties = pd.read_csv(fuel_properties)
    properties["mjpl"] = properties["density_kgpl"] * properties["ncv_mjpkg"]
    properties["mj_per_bbl"] = properties["mjpl"] * LITRES_PER_BARREL
    properties["gj_per_bbl"] = properties["mj_per_bbl"] / 1e3
    properties = properties[["Fuel_TIMES", "gj_per_bbl"]]
    return properties

    # need to convert to NZD/GJ


def get_imported_fuel_costs(imported_fuels):
    """
    Reads fuel cost assumptions assuming in USD/bbl
    Converts to NZD/GJ
    Uses an input list of imported fuels - only calculates for these s
    """

    df = pd.read_csv(price_assumptions)

    # join codes
    conc = pd.read_csv(fuel_codes)
    df = df.merge(conc, on="Fuel", how="left")

    # join properties
    df = df.merge(get_fuel_gj_per_barrel(), on="Fuel_TIMES", how="left")

    df["usdbbl_to_nzd_gj"] = USD_TO_NZD / df["gj_per_bbl"]

    # convert and relabel USD/BBL
    df["Value"] = np.where(
        df["Unit"] == "USD/bbl", df["Value"] * df["usdbbl_to_nzd_gj"], df["Value"]
    )
    df["Unit"] = np.where(df["Unit"] == "USD/bbl", "NZD/GJ", df["Unit"])

    # filter for only imported items
    df = df[df["Fuel_TIMES"].isin(imported_fuels)]
    # strict unit checking
    df = df[df["Unit"] == "NZD/GJ"]

    # define techname and commodity
    df["TechName"] = "IMP" + df["Fuel_TIMES"]
    df["Comm-Out"] = df["Fuel_TIMES"]

    # this is just cost!
    df["Attribute"] = "Cost"

    df = df[["TechName", "Comm-Out", "Attribute", "Year"]]

    return df


def main():
    """
    Entry point - coordinates script
    """
    OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)

    # deliverability forecasts
    df = pd.read_csv(gas_file)

    df = aggregate_fields(df, FIELD_MAPPING)

    df_2p = get_veda_deliverability(df, resource_types=["2P"])
    df_2p.to_csv(OUTPUT_LOCATION / "deliverability_forecasts_2p.csv", index=False)

    df_all = get_veda_deliverability(df, resource_types=["2P", "2C"])
    df_all.to_csv(
        OUTPUT_LOCATION / "deliverability_forecasts_2p_and_2c.csv", index=False
    )

    # nga costs and emissions
    df_nga_costs_emissions = get_nga_costs_emissions()
    df_nga_costs_emissions.to_csv(
        OUTPUT_LOCATION / "natural_gas_production_costs_emissions.csv", index=False
    )

    import_costs = get_imported_fuel_costs(["PET", "DSL", "FOL", "JET", "LPG"])
    import_costs.to_csv(OUTPUT_LOCATION / "imported_fuel_costs.csv")


if __name__ == "__main__":
    main()
