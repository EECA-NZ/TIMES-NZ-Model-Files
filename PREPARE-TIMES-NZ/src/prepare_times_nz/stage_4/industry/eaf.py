"""
Builds EAF demand projections and the relevant steel cogen reductions

to represent NZSteel transitioning to an EAF recycler.

Note: the EAF implementation also requires other inputs, which are not scripted here.

These are:
a) subres files built to identify the new processes and commodities
b) demand reductions for pure steel processes, such as coal feedstock for reduction

This module only creates demand projections for the new recycled steel commodity
and fixes the cogeneration levels in place (cogen falls when facility transitions from coal).

"""

import numpy as np
import pandas as pd
from prepare_times_nz.stage_0.stage_0_settings import BASE_YEAR
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.filepaths import STAGE_4_DATA

# CONSTANTS

EAF_INSTALL_1 = 2026  # first install date (confirmed)
EAF_INSTALL_2 = 2036  # second install date (only for a specific scenario)
EAF_GW = 0.03  # 30 MW install
EAF_PJ = EAF_GW * 31.536  # standard GW/PJ
COGEN_PJ = 1.9426176  # from data (would be better to read directly!)
END_YEAR = 2050

EAF_DEMAND_CODE = "STEEL_FURNC-RSTEEL"
STEEL_COGEN_CODE = "ELC_CoalCHP_GlenbrookSteel"

OUTPUT_LOCATION = STAGE_4_DATA / "scen_demand/eaf"


def create_eaf_demand():
    """
    Compiles input constants into series of demand
    and activity projections for the EAF

    NOTE: the steel commodities with reduced demand are handled separately

    """
    df = pd.DataFrame()

    df["Year"] = range(BASE_YEAR, END_YEAR + 1)

    # expand for scenarios
    df_a = df.assign(Scenario="Traditional")
    df_b = df.assign(Scenario="Transformation")

    df = pd.concat([df_a, df_b], ignore_index=True)

    # add eaf count
    df["eaf_count"] = np.where(df["Year"] >= EAF_INSTALL_1, 1, 0)
    df["eaf_count"] = np.where(
        (df["Year"] >= EAF_INSTALL_2) & (df["Scenario"] == "Transformation"),
        df["eaf_count"] + 1,
        df["eaf_count"],
    )

    # use eaf count to assign key variables
    # EAF demand:
    df[EAF_DEMAND_CODE] = EAF_PJ * df["eaf_count"]
    # halve the cogen output for each eaf installation
    df[STEEL_COGEN_CODE] = COGEN_PJ * (1 - df["eaf_count"] / 2)

    return df


def create_eaf_file(df, scenario, category):
    """
    Pulls the scenario/measure from the created data
    and creates a single veda output file to save
    """

    df = df[df["Scenario"] == scenario].copy()
    df = df[["Year", category]]
    df["Source"] = category

    # define key veda inputs

    attribute = ""
    interp = ""
    type_varname = ""
    limtype = ""

    if category == EAF_DEMAND_CODE:
        attribute = "Demand"
        interp = "2"
        type_varname = "Cset_CN"

    elif category == STEEL_COGEN_CODE:
        attribute = "ACT_BND"
        limtype = "FX"
        interp = "5"
        type_varname = "Pset_PN"

    else:
        raise ValueError("please review the EAF Veda inputs!")

    # apply and reshape

    df["0"] = interp
    df["TimeSlice"] = ""
    df["Region"] = "NI"
    df["Attribute"] = attribute
    df["LimType"] = limtype
    df[type_varname] = category

    index_vars = ["TimeSlice", "Region", "Attribute", "LimType", type_varname, "0"]

    # pivot years
    df = (
        df.pivot(columns="Year", values=category, index=index_vars)
        .reset_index()
        .rename_axis(None, axis=1)
    )

    return df


def write_eaf_file(df, scenario, category):
    """
    A wrapper to generate the required file and save it with some parameters for names/labels

    """

    if category == "eaf_demand":
        code = EAF_DEMAND_CODE
    elif category == "steel_cogen":
        code = STEEL_COGEN_CODE
    else:
        raise ValueError("Unknown category input, please review")

    # create data
    out = create_eaf_file(df, scenario, code)

    # generate name and label

    filename = f"{category}_{scenario.lower()}.csv"
    filelabel = f"Saving {scenario} {category}"

    # save
    _save_data(out, name=filename, label=filelabel, filepath=OUTPUT_LOCATION)


def main():
    """Entrypoint"""
    df = create_eaf_demand()

    write_eaf_file(df, "Traditional", "eaf_demand")
    write_eaf_file(df, "Traditional", "steel_cogen")
    write_eaf_file(df, "Transformation", "eaf_demand")
    write_eaf_file(df, "Transformation", "steel_cogen")


if __name__ == "__main__":
    main()
