"""

This module distributes the contingent natural gas reserves across each applicable field

This includes contingent gas from fields that haven't been developed yet.


"""

# some conflict between pylint and isort here
# pylint: disable = wrong-import-order
import numpy as np
import pandas as pd
from prepare_times_nz.utilities.filepaths import STAGE_1_DATA, STAGE_3_DATA
from scipy.stats import lognorm

# identify required input files

MBIE_DATA = STAGE_1_DATA / "mbie"
GAS_FORECASTS = MBIE_DATA / "natural_gas_forecasts.csv"
CONTINGENT_FILE = MBIE_DATA / "contingent_reserves.csv"
OUTPUT_LOCATION = STAGE_3_DATA / "oil_and_gas"


OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)
# Constants -----------------------------------------------------------

CONTINGENT_SHARE_ASSUMPTION = 0.6


# Functions -----------------------------------------------------------


def get_contingent_for_field(
    field, contingent_file=CONTINGENT_FILE, share_assumption=CONTINGENT_SHARE_ASSUMPTION
):
    """Returns the natural gas reserves as a value
    for a given field

    Currently touches the input file a lot more than possibly needed

    """

    df = pd.read_csv(contingent_file)

    df = df[df["Fuel"] == "Natural gas"]
    df = df[df["Field"] == field]
    if len(df) == 0:
        return 0
    return df["Value"].item() * share_assumption


def get_contingent_start_year_for_field(field, df):
    """
    Based on the input df of production shapes,
    return a list of fields and the year contingent can begin
    Takes the earlist max year for each field, adds one, returns a list of field to year
    """
    # filter main data to field
    df = df[df["Field"] == field]
    # filter to max output
    df = df[df["Value"] == max(df["Value"])]

    # there may be multiple years but we just take the earliest
    # we add 1 (contingent release begins the year after max)

    return df["Year"].iloc[0] + 1


def get_max_output_of_field(field, df):
    """returns the maximum value for a field
    This defaults to the forecast 2P output"""
    df = df[df["Field"] == field]

    return df["Value"].max().item()


def _get_value_for_year(df, year, var="Value"):
    vals = df.loc[df["Year"] == year, var]
    if vals.empty:
        return 0
    # else
    return vals.iloc[0]  # first match


def distribute_new_gas(field, start_year, sigma=0.8, years=40, startup=2):
    """
    Pull a field's contingent values out and distribute them lognormally
    Field: the name of the field to get contingent values for (will also label output)
    start_year: the first year of production
    startup: number of years before reaching peak production
    sigma: variance/spread for lognormal distribution
    years: years to distribute this over

    """

    contingent = get_contingent_for_field(field)

    peak_year = startup + 1
    mu = np.log(peak_year) + sigma**2
    x = np.arange(1, years + 1)

    pdf = lognorm.pdf(x, s=sigma, scale=np.exp(mu))
    weights = pdf / pdf.sum()
    allocation = contingent * weights

    df = pd.DataFrame({"Year": x, "Value": allocation})

    df["Year"] = df["Year"] + start_year - 1
    df["Variable"] = "Natural gas forecasts"
    df["ResourceType"] = "2C"
    df["Unit"] = "PJ"
    df["Field"] = field

    return df


def decay_field_contingent(field, df):
    """

    Takes a field. Returns the contingent decayed


    """

    # expecting the input to just have the one field. Ensure that's true here

    contingent = get_contingent_for_field(field)
    cstart = get_contingent_start_year_for_field(field, df)
    max_possible = get_max_output_of_field(field, df)

    # calculate remaining 2p from contingent start and existing decay rates
    df = df[df["Field"] == field]
    df = df[df["Year"] >= cstart]
    df["Remaining2PAtStart"] = df.groupby("Field").transform("sum")["Value"]
    df["Decay"] = df["Value"] / df["Remaining2PAtStart"]
    df["TotalToDistribute"] = df["Remaining2PAtStart"] + contingent

    # contingent start year
    to_distribute = df["TotalToDistribute"].iloc[0]
    decay = df["Decay"].iloc[0]

    # some decay rate tinkering:

    if field == "Kupe":
        decay = 0.15

    years_tail = np.arange(cstart, int(df["Year"].max()) + 100)  # generous horizon

    rows = []
    for i, y in enumerate(years_tail):
        # how much 2P was that year
        existing_2p = _get_value_for_year(df, y)
        # we distribute the remaining by taking the decay from what's left
        q = to_distribute * decay
        # then ensure it's not less than 2p projections, or more than max
        q = min(q, max_possible)
        q = max(q, existing_2p)

        # remove the distributed from total distribution
        to_distribute -= q
        # we've distributed the sum of remaining 2p and contingent,
        # so we split these by checking against the 2p for that year (rest was contingent)
        contingent_release = q - existing_2p

        rows.append(
            {
                "Index": i,
                "Year": y,
                "ToDistribute": to_distribute,
                "TotalOutput": q,
                "2C": contingent_release,
            }
        )

    # combine
    result_df = pd.DataFrame(rows)
    # label and output
    result_df["Field"] = field
    result_df = result_df[["Year", "Field", "2C"]]

    return result_df


def distribute_all_field_contingents(df):
    """

    A wrapper method to run contingent distribution for all fields

    Identifies fields in the list and combines results before tidying
    """
    df = df[df["Field"] != "Total"]
    fields = df["Field"].unique()

    contingent_df = pd.DataFrame()
    for field in fields:
        df_field = decay_field_contingent(field, df)
        contingent_df = pd.concat([contingent_df, df_field])

    out = pd.merge(df, contingent_df, how="left")
    out["2C"] = out["2C"].fillna(0)

    # pivot
    out = out.rename(columns={"Value": "2P"})
    value_vars = ["2P", "2C"]
    id_vars = [col for col in out.columns if col not in value_vars]
    out = out.melt(
        id_vars=id_vars,
        value_vars=value_vars,
        var_name="ResourceType",
        value_name="Value",
    )

    return out


# execute  ------------------------------------------------------------------------------


def main():
    """script entrypoint"""

    # read data
    forecast_df = pd.read_csv(GAS_FORECASTS)

    # create new fields (just karewa right now)
    df_new_fields = distribute_new_gas("Karewa", start_year=2035, sigma=0.8, startup=2)
    # distribute contingents to existing
    df = distribute_all_field_contingents(forecast_df)
    # combine
    df = pd.concat([df, df_new_fields])
    # save
    df.to_csv(OUTPUT_LOCATION / "oil_and_gas_projections.csv", index=False)


if __name__ == "__main__":
    main()
