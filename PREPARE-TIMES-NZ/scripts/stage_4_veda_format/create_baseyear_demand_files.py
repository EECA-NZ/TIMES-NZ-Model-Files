"""
Runs all baseyear veda file processing for each demand sector:
 - Ag/Forest/Fishing
 - Commercial
 - Industrial
 - Residential
 - Transport
"""

from prepare_times_nz.stage_4.baseyear.ag_forest_fish import main as ag
from prepare_times_nz.stage_4.baseyear.commercial import main as com
from prepare_times_nz.stage_4.baseyear.industrial import main as ind
from prepare_times_nz.stage_4.baseyear.residential import main as res
from prepare_times_nz.stage_4.baseyear.transport import main as tra


def main():
    """
    Orchestrates all scripts
    """
    ag()
    com()
    ind()
    res()
    tra()


if __name__ == "__main__":
    main()
