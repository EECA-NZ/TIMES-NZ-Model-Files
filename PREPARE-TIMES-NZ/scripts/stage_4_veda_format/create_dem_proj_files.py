"""
Orchestrates building of Veda files for demand projections
"""

from prepare_times_nz.stage_4.demand_projections.demand_drivers import (
    main as demand_drivers,
)
from prepare_times_nz.stage_4.demand_projections.driver_allocations import (
    main as driver_allocations,
)


def main():
    """
    Orchestrates building of Veda files for demand projections
    Pulls the drivers and the allocations.

    Drivers are a series of indexes that we can grow demand by,
    and these keep the same ID but can shift per scenario

    Allocations assign commodity demand to drivers

    """

    demand_drivers()
    driver_allocations()


if __name__ == "__main__":
    main()
