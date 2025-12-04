"""
This script simply executes and builds all demand projection calculations for various scenarios
Note that it really only handles the complex ones, like industry
Simpler ones are just handled directly in stage 4.
"""

# pylint: disable=expression-not-assigned
from prepare_times_nz.stage_3.demand_projections.agriculture import (
    main as agriculture_demand_projections,
)
from prepare_times_nz.stage_3.demand_projections.datacentre import (
    main as datacentre_demand_projections,
)
from prepare_times_nz.stage_3.demand_projections.industry import (
    main as industry_demand_projections,
)
from prepare_times_nz.stage_3.demand_projections.transport import (
    main as transport_demand_projections,
)


def main():
    """Entrypoint"""
    industry_demand_projections(),
    datacentre_demand_projections(),
    agriculture_demand_projections(),
    transport_demand_projections()


if __name__ == "__main__":
    main()
