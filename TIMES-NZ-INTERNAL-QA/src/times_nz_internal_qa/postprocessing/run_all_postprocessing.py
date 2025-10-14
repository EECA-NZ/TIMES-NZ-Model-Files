"""
Orchestrates each component of postprocessing
"""

from times_nz_internal_qa.postprocessing.define_data import main as define_data
from times_nz_internal_qa.postprocessing.get_data import main as get_data
from times_nz_internal_qa.postprocessing.process_data import main as process_data

REDEFINE_DATA = False


def main():
    """entrypoint"""
    if REDEFINE_DATA:
        define_data()
    get_data()
    process_data()


if __name__ == "__main__":
    main()
