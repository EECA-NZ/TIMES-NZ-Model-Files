"""
This module loads our processed oil and gas data and creates three outputs:

1) deliverability forecasts (multiple versions)
2) natural gas fugitive emissions and costs (these are applied to the field processes)
3) imported fuel cost assumptions, incl usd/bbl - NZD/GJ conversions

"""

import numpy as np
import pandas as pd
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.filepaths import (
    ASSUMPTIONS,
    CONCORDANCES,
    STAGE_3_DATA,
    STAGE_4_DATA,
)

# CONSTANTS

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

# Helpers ----------------------------------------------------------------------


def save_og_data(df, name):
    """Wrapper for save function"""
    _save_data(df, name, label="Oil & Gas for Veda", filepath=OUTPUT_LOCATION)


# Functions ----------------------------------------------------------------------


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
    df = df.rename(columns={"Value": "NI"})
    # df["Region"] = "NI"

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
        columns={"TIMES_Field": "TechName", "Emissions_Factor": "ENV_ACT~GASCO2~NI"}
    )
    return df


def get_nga_paramaters():
    """Combines the costs and emissions data for a single table
    Uses the field codes listed in the emissions file
    and attaches costs to all of these
    Ensures output commodity is declared"""
    costs = get_natural_gas_price_forecasts()
    efs = get_natural_gas_fugitive_emissions()

    df = efs.merge(costs, how="cross")
    df["Comm-OUT"] = "NGA"

    # ensure the outputs include
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
    save_og_data(df_2p, "deliverability_forecasts_2p.csv")

    df_all = get_veda_deliverability(df, resource_types=["2P", "2C"])
    save_og_data(df_all, "deliverability_forecasts_2p_and_2c.csv")

    # nga costs and emissions
    df_nga_parameters = get_nga_paramaters()
    df_nga_parameters.to_csv(
        OUTPUT_LOCATION / "natural_gas_production_parameters.csv", index=False
    )

    import_costs = get_imported_fuel_costs(["PET", "DSL", "FOL", "JET", "LPG"])
    save_og_data(import_costs, "imported_fuel_costs.csv")


if __name__ == "__main__":
    main()
