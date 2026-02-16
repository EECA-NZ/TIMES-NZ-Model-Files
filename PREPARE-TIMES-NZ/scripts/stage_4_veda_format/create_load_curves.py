"""
Orchestrates building of Veda files for demand projections
"""

from prepare_times_nz.stage_4.load_curves import main as load_curves


def main():
    """
    Creates veda files for load curves
    (also known as the COM_FR scenarios)
    """
    load_curves()


if __name__ == "__main__":
    main()
