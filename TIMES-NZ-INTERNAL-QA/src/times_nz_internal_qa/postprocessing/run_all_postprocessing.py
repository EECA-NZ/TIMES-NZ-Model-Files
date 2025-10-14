"""
Orchestrates each component of postprocessing
"""

from times_nz_internal_qa.postprocessing.define_data import main as define_data
from times_nz_internal_qa.postprocessing.get_data import main as get_data
from times_nz_internal_qa.postprocessing.process_data import main as process_data

# SWITCHES
# this requires a local fresh run of PREPARE-TIMES-NZ to be populated.
# It's often not necessary to rerun, unless process_data() reports missing items
REDEFINE_DATA = False
# this expects a Veda installation with scenario results in your windows mount under your username
# You would rerun this if you had run the model and needed to refresh your results
IMPORT_FROM_VEDA = False


def main():
    """entrypoint"""
    if REDEFINE_DATA:
        define_data()
    if IMPORT_FROM_VEDA:
        get_data()
    # this is required to produce the app input files
    process_data()


if __name__ == "__main__":
    main()
