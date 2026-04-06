"""
Orchestrates building of Veda files for demand projections
"""

from prepare_times_nz.stage_4.load_curves import main as load_curves
from prepare_times_nz.stage_4.technology_af_curves import main as tech_af_curves


def main():
    """
    Creates veda files for load curves
    (also known as the COM_FR scenarios)
    As well as the technology AFs for some technologies
    """
    load_curves()
    tech_af_curves()


if __name__ == "__main__":
    main()
