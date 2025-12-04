"""
This script orchestrates all our various definitions
It does not process scenario data. Rather, it collects and defines
categories for all process and commodity codes that we expect to be in the scenario file

This means that it doesnt necessarily need to be run on additional model runs

However, if you add some new process or commodity in PREPARE-TIMES-NZ,
Like in a new subres,
You may wish to enhance this method's ability to categorise the new additions
"""

from times_nz_internal_qa.postprocessing.get_definitions.closure_processes import (
    main as closures,
)
from times_nz_internal_qa.postprocessing.get_definitions.demand_processes import (
    main as demand_processes,
)
from times_nz_internal_qa.postprocessing.get_definitions.distribution_processes import (
    main as distribution_processes,
)
from times_nz_internal_qa.postprocessing.get_definitions.elec_processes import (
    main as elec_processes,
)
from times_nz_internal_qa.postprocessing.get_definitions.energy_commodities import (
    main as energy_commodities,
)
from times_nz_internal_qa.postprocessing.get_definitions.sets_and_units import (
    main as sets_and_units,
)
from times_nz_internal_qa.postprocessing.get_definitions.transport_patch import (
    main as transport_patch,
)


def main():
    """
    Orchestrates all set definitions
    """

    # patches (currently just transport)
    transport_patch()
    # extracting sets and units from PREPARE-TIMES-NZ
    sets_and_units()
    # All commodities
    energy_commodities()
    # Processes by group
    elec_processes()
    demand_processes()
    distribution_processes()
    # closure processes
    closures()


if __name__ == "__main__":
    main()
