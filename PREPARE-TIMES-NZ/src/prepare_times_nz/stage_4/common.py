"""
This module stores some replicable patterns that are often useful in
building Veda tables

"""

import pandas as pd


def add_extra_input_to_topology(df, processes_to_expand, new_input):
    """
    A method for adding an extra input option for base year parameters

    Works by duplicating existing process information but changing the Comm-IN

    input df  must have process codes under 'TechName'
        and standard 'Comm-IN'/'Comm-OUT' variables
        as expected in baseyear FI_T tables

    """

    # if a tech could use these fuels, we say it can also use biogas
    # all other parameters remain the same
    new_input_df = df[df["TechName"].isin(processes_to_expand)].copy()
    # tech can use biogas
    new_input_df["Comm-IN"] = new_input
    # set the base activity for these to 0
    new_input_df["ACT_BND"] = 0
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
