"""
Processing methods for WEM (winter energy margin)

The idea here is we want to enforce capacity generation margins during winter/autumn.

This is done by first assessing all of our plant's capacity factors during these months.

For intermittent plants, these are weighted averages of our AFs for these months

(ie the sum of the AF weighted by the YRFR)

For dispatchable plants, it's just the regular AF

Then, these are set to the LHS of the constraint

We can then add the effective RHS as a function of the demand/CAP2ACT

This is effectively an energy constraint but expressed as a capacity one


NOTE:

When originally writing this, we assumed that only the capacity
     factors needed to be calculated from other data
However, actually the technology's island availability
    and output commodities are also important for the user constraint.
This method could be made much much much more robust by extracting
    that data from the system rather than doing some hardcoding here

"""

import numpy as np
import pandas as pd
from prepare_times_nz.stage_0.stage_0_settings import BASE_YEAR
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.filepaths import ASSUMPTIONS, STAGE_2_DATA, STAGE_3_DATA

OUTPUT_LOCATION = STAGE_3_DATA / "wem_user_constraints"

yrfr_data = STAGE_2_DATA / "settings/load_curves/yrfr.csv"


# Helpers -----------------------------------------------


def save_wem_data(df, name):
    """
    wrapper for saving wem outputs
    """
    _save_data(
        df=df, name=name, label="UC_WEM constraint table", filepath=OUTPUT_LOCATION
    )


# FUnctions -----------------------------------------------


def get_baseyear_tech_afs():
    """
    Return all plant tech types and capacity factors (availability factors)
    from base year data
    Label these as default capacity factors

    Should probably load these directly from assumptions!
    """

    df = pd.read_csv(STAGE_2_DATA / "electricity/base_year_electricity_supply.csv")
    df = df[df["Variable"] == "CapacityFactor"]
    df = df[["Tech_TIMES", "Value"]].drop_duplicates()
    df = df.rename(columns={"Value": "DefaultCapacityFactor"})

    return df


def get_subres_tech_afs():
    """
    Return default tech assumptions for future Tech_TIMES codes
    Pulled directly from assumptions files
    """

    df = pd.read_csv(
        ASSUMPTIONS / "electricity_generation/future_techs/TechnologyAssumptions.csv"
    )

    df = df[["Tech_TIMES", "AFA"]].drop_duplicates()

    df = df[~df["AFA"].isnull()]

    df = df.rename(columns={"AFA": "DefaultCapacityFactor"})

    return df


def get_default_afs():
    """Combine the default assumptions for base year and future techs"""

    df_b = get_baseyear_tech_afs()
    df_y = get_subres_tech_afs()

    df = pd.concat([df_b, df_y]).drop_duplicates()

    df = df.sort_values("Tech_TIMES")
    return df


def get_af_curves():
    """
    Load ren_af assumptions

    """

    df = pd.read_csv(
        ASSUMPTIONS / "electricity_generation/renewable_curves/RenewableCurves.csv"
    )

    if "TechCode" in df.columns:
        df = df.rename(columns={"TechCode": "Tech_TIMES"})

    return df


def get_yrfr():
    """Load year fraction data"""
    df = pd.read_csv(yrfr_data)
    return df


def get_yrfr_seasons(df):
    """
    reads the yrfr data and aggregates to seasons
    Does this by just taking the first 4 chars of the timeslice code
    Then sums
    """
    df = df.copy()  # dont mutate external table
    df["TimeSlice"] = df["TimeSlice"].str[:4]
    df = df.groupby("TimeSlice").sum().reset_index()
    return df


def get_ni_only_techs():
    """
    returns a list of all base year techs only available in the NI
    Includes some specific hardcoded ones that weren't in base year data
    The non base year techs should be handled better - sorry
    """

    hardcoded_ni_techs = ["WindFloatOff"]
    # base year from main data
    by_islands = pd.read_csv(
        STAGE_2_DATA / "electricity/base_year_electricity_supply.csv"
    )
    by_islands = by_islands[["Tech_TIMES", "Region"]].drop_duplicates()

    techs_in_ni = by_islands[by_islands["Region"] == "NI"]["Tech_TIMES"].tolist()
    techs_in_si = by_islands[by_islands["Region"] == "SI"]["Tech_TIMES"].tolist()

    ni_only = [
        tech for tech in techs_in_ni if tech not in techs_in_si
    ] + hardcoded_ni_techs

    return ni_only


def get_si_only_techs():
    """
    extremely complex function to return a list of all techs only available in SI
    """
    return ["HydRR"]


def get_weighted_winter_afs():
    """
    Calculates weighted average availability for techs
    with seasonal availablity
    Filters these for winter/autumn seasons

    outputs different availability per tech/island
    """

    # get availability curves for intermittent techs
    df = get_af_curves()
    # get the daynite year fractions
    yrfr = get_yrfr()
    # get the seasonal year fractions
    yrfr_seasons = get_yrfr_seasons(yrfr)

    # combine the list of all year fractions
    all_yrfr = pd.concat([yrfr, yrfr_seasons])

    # join to af curves (either daynite or seasonal types)

    df = df.merge(all_yrfr, on="TimeSlice", how="left")

    # calc weighted availability

    df["NI"] = df["NI"] * df["YRFR"]
    df["SI"] = df["SI"] * df["YRFR"]

    # aggregate to season

    df["TimeSlice"] = df["TimeSlice"].str[:4]

    # filter for winter and autumn
    df = df[df["TimeSlice"].isin(["WIN-", "FAL-"])]
    # no longer need this
    df = df.drop("TimeSlice", axis=1)
    # now we aggregate by tech for winter/autumn availability
    df = df.groupby(["Tech_TIMES"]).sum().reset_index()

    # currently, the value is the availability of that tech in that season
    # compared to the whole year
    # so to get an average availability over the year we go back the other way

    df["NI"] = df["NI"] / df["YRFR"]
    df["SI"] = df["SI"] / df["YRFR"]

    return df


def get_winter_share():
    """Simply return the winter/fall share of the year"""
    # get the daynite year fractions
    df = get_yrfr()
    # get the seasonal year fractions
    df = get_yrfr_seasons(df)
    # filter winter fall
    df = df[df["TimeSlice"].isin(["FAL-", "WIN-"])]
    # sum
    return df["YRFR"].sum()


def get_all_afs():
    """
    Takes all techs from the default and weighted AFs
    Creates a single table where we use the weighted AFs if they exist
    Otherwise uses default
    """

    df_default = get_default_afs()

    df_intermittent = get_weighted_winter_afs()

    # first start by just ensuring that we have every tech from either table
    df = pd.concat([df_default, df_intermittent])

    df = df[["Tech_TIMES"]].drop_duplicates()

    ni_techs = get_ni_only_techs()
    si_techs = get_si_only_techs()
    # add details from both tables

    df = df.merge(df_default, how="left", on="Tech_TIMES")
    df = df.merge(df_intermittent, how="left", on="Tech_TIMES")

    # select caps to use per tech
    df["UC_CAP~SI"] = df["SI"].fillna(df["DefaultCapacityFactor"])
    df["UC_CAP~NI"] = df["NI"].fillna(df["DefaultCapacityFactor"])

    # trim to just needed outputs
    df = df[["Tech_TIMES", "UC_CAP~SI", "UC_CAP~NI"]]

    # make SI value NA if the tech is NI only
    df.loc[df["Tech_TIMES"].isin(ni_techs), "UC_CAP~SI"] = np.nan
    # and vice versa
    df.loc[df["Tech_TIMES"].isin(si_techs), "UC_CAP~NI"] = np.nan

    return df


def get_flo_equation(margin, cap2act=31.536, year_fraction=1):
    """Creates the output expected by the uc_flo equation
    Effectively converting the margin into an amount of expected capacity
    This requires the cap2act factor and also the share of the year

    The default share is 1 but later we'll insert the winter share
    as this is applied to winter demand

    The resulting value will be applied as a coefficient to activity output
    """

    flo = (margin + 1) / cap2act
    flo = flo / year_fraction
    # flip sign to balance against cap in UC
    flo = flo * -1
    return flo


def create_uc_table(df, uc_n, uc_type, uc_desc, margin):
    """
    Uses the AFs produced and reshaped for the
    user_constraint

    uc_n = name of UC (eg WEM, WEM_SI)
    uc_type = specific code for the method (UC_RHRST, etc)
    uc_desc = user description of UC
    """

    # get AF wildcards
    df["Pset_PN"] = "ELC_" + df["Tech_TIMES"] + "_*"
    df["Pset_CO"] = "ELC"
    df.loc[df["Tech_TIMES"] == "SolarDist", "Pset_CO"] = "ELCDD"
    # remove steel cogen, which contributes only to ELC
    # (it reduces overall ELCDD demand so does contribute,
    #  just not to the constraint directly)

    df = df[df["Tech_TIMES"] != "CoalCHP"].copy()

    # add some labels (first row only, using df.loc[0])

    # input specific params
    df.loc[0, "UC_N"] = uc_n

    df.loc[0, f"{uc_type}~NI"] = 0
    df.loc[0, f"{uc_type}~SI"] = 0
    df.loc[0, f"{uc_type}~0"] = 5
    df.loc[0, "LimType"] = "LO"
    df.loc[0, "UC_Desc"] = uc_desc

    # create the demand side (we'll append this afterwards)
    df_d = pd.DataFrame()

    winter_share = get_winter_share()
    uc_flo = get_flo_equation(margin=margin, year_fraction=winter_share)
    # set single row with the coefficient
    df_d.loc[0, "UC_FLO"] = uc_flo

    # add the additional params. df has only one row so no need for df.loc[]
    df_d["TimeSlice"] = "FAL-,WIN-"
    df_d["Cset_CN"] = "ELCDD"
    df_d["Pset_PN"] = "G_ELC_LV"

    # combine
    df = pd.concat([df, df_d])

    # define year
    df["Year"] = BASE_YEAR + 1  # to check that default extrapolation works here

    return df


def make_uc_wem(df):
    """
    Additional manipulation of the uc created above specific to the
    national constraint
    """

    out = create_uc_table(df, "WEM", "UC_RHSTS", "NZ Winter energy margin", margin=0.16)

    # relabel the UC_RHSTS to ignore islands.
    # Because its always 0 it doesn't matter which we pick.
    out["UC_RHSTS"] = out["UC_RHSTS~NI"]

    out = out[
        [
            "UC_N",
            "TimeSlice",
            # "Pset_Set",
            "Pset_PN",
            "Pset_CO",
            "Cset_CN",
            # "Attribute",
            "Year",
            "LimType",
            "UC_CAP~NI",
            "UC_CAP~SI",
            "UC_FLO",
            "UC_RHSTS",
            "UC_RHSTS~0",
            "UC_Desc",
        ]
    ]

    return out


def make_uc_wem_si(df):
    """
    Additional manipulation of the uc created above specific to the
    national constraint
    """

    # first, filter out all the null SI capacites for NI only techs
    df_for_si = df[~df["UC_CAP~SI"].isnull()].copy().reset_index()

    out = create_uc_table(
        df_for_si, "WEM_SI", "UC_RHSRTS", "SI Winter energy margin", margin=0.3
    )

    # only relevant capacity factor coefficient is the SI one

    out["UC_CAP"] = out["UC_CAP~SI"]

    out = out[
        [
            "UC_N",
            "TimeSlice",
            # "Pset_Set",
            "Pset_PN",
            "Pset_CO",
            "Cset_CN",
            # "Attribute",
            "Year",
            "LimType",
            "UC_CAP",
            "UC_FLO",
            "UC_RHSRTS~NI",
            "UC_RHSRTS~SI",
            "UC_RHSRTS~0",
            "UC_Desc",
        ]
    ]

    return out


def main():
    """Script entrypoint"""

    df = get_all_afs()

    uc_wem = make_uc_wem(df)
    uc_wem_si = make_uc_wem_si(df)

    save_wem_data(uc_wem, "uc_wem.csv")
    save_wem_data(uc_wem_si, "uc_wem_si.csv")


if __name__ == "__main__":
    main()
