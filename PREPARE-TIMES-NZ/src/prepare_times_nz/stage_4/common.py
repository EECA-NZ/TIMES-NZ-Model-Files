"""
This module stores some replicable patterns that are often useful in
building Veda tables

"""

import pandas as pd


def apply_share_constraints(df, share_constraints=None):
    """Apply optional share constraints to copied topology rows."""
    if share_constraints is None:
        return df

    base_year_share_up = share_constraints.get("base_year_share_up")
    future_share_year = share_constraints.get("future_share_year")
    future_share_up = share_constraints.get("future_share_up")

    if base_year_share_up is not None:
        df["Share-I~UP"] = base_year_share_up
    if future_share_year is not None and future_share_up is not None:
        df[f"Share-I~UP~{future_share_year}"] = future_share_up

    return df


def add_extra_input_to_topology(
    df,
    processes_to_expand,
    new_input,
    share_constraints=None,
):
    """
    A method for adding an extra input option for base year parameters

    Works by duplicating existing process information but changing the Comm-IN

    input df  must have process codes under 'TechName'
        and standard 'Comm-IN'/'Comm-OUT' variables
        as expected in baseyear FI_T tables

    Optional share constraints can be added to keep the new input unavailable
    in the base year while allowing it in later years.
    """

    # if a tech could use these fuels, we say it can also use biogas
    # all other parameters remain the same
    new_input_df = df[df["TechName"].isin(processes_to_expand)].copy()
    # tech can use biogas
    new_input_df["Comm-IN"] = new_input
    # ACT_BND is a process-level base-year activity. Leave it blank on copied
    # input rows so we don't double-count demand or accidentally fix the
    # multi-input process activity through the duplicate row.
    if "ACT_BND" in new_input_df.columns:
        new_input_df["ACT_BND"] = pd.NA
    new_input_df = apply_share_constraints(new_input_df, share_constraints)
    # add to main table
    df = pd.concat([df, new_input_df])
    # sort for clearer reads
    df = df.sort_values(["TechName", "Comm-IN"])

    return df


def get_processes_with_input_commodity(df, input_commodity):
    """
    With a df containing 'TechName' and 'Comm-IN',
    returns the list of processes that use the specified input_commodity in "Comm-IN"

    """

    processes = df[df["Comm-IN"].isin([input_commodity])].copy()
    process_list = processes["TechName"].unique().tolist()

    return process_list
