"""
This module stores some replicable patterns that are often useful in
building Veda tables


"""

import numpy as np


def ensure_no_build_if_free(df, invcost_var="INVCOST"):
    """
    Checks an invcost var in a dataframe. If this is null, ensures that:
      NCAP_BND is 0
      NCAP_BND~0 is 5
    This will force this process to never be built in any model year

    We build these as strings
    """

    # First, we don't want to overwrite other settings for these vars.
    # If they don't exist, we add blank entries,
    # but otherwise keep whatever is there

    if "NCAP_BND" not in df.columns:
        df["NCAP_BND"] = ""

    if "NCAP_BND~0" not in df.columns:
        df["NCAP_BND~0"] = ""

    # now we populate them for null investments

    df["NCAP_BND"] = np.where(df[invcost_var].isna(), "0", df["NCAP_BND"])
    df["NCAP_BND~0"] = np.where(df[invcost_var].isna(), "5", df["NCAP_BND~0"])

    return df
