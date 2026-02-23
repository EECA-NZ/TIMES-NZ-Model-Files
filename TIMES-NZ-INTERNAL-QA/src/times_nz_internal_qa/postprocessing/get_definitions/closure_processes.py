"""
Defines processes we use to represent dynamic demand device closures
These just remove energy from the system when prices are too high
and effectively represent deindustrialisation
Because the demand is removed from the system, we don't need to show these,
We simply categorise them in our results
"""

import pandas as pd
from times_nz_internal_qa.utilities.filepaths import PROCESS_CONCORDANCES


def process_closures():
    """Defines which processes represent closures"""

    closure_processes = [
        "UREA-NGA-REFRM-PH_HIGH-CLOSURE",
        "UREA-NGA-COMPR-MTV_STA-CLOSURE",
        "UREA-NGA-FDSTK-FDSTK-CLOSURE",
        "METH-NGA-REFRM-PH_HIGH-CLOSURE",
        "METH-NGA-FDSTK-FDSTK-CLOSURE",
    ]

    df = pd.DataFrame()
    df["Process"] = closure_processes

    df.to_csv(PROCESS_CONCORDANCES / "closures.csv", index=False, encoding="utf-8-sig")


def main():
    """Entrypoint"""
    process_closures()


if __name__ == "__main__":
    main()
