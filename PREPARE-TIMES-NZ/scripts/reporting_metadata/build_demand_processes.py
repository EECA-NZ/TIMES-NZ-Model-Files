"""Write PREP-owned demand-device reporting metadata."""

import pandas as pd
from prepare_times_nz.reporting_metadata.demand import (
    build_agriculture_processes,
    build_commercial_processes,
    build_demand_commodities,
    build_industry_processes,
    build_residential_processes,
    build_transport_processes,
    combine_demand_processes,
)
from prepare_times_nz.utilities.filepaths import (
    ASSUMPTIONS,
    DATA_INTERMEDIATE,
    STAGE_2_DATA,
    STAGE_4_DATA,
)

OUTPUT_DIR = DATA_INTERMEDIATE / "postprocessing_metadata"
REPORTING_ASSUMPTIONS = ASSUMPTIONS / "reporting"


def main():
    """Read prepared demand inputs and write their reporting catalogs."""
    processes = combine_demand_processes(
        [
            build_industry_processes(
                pd.read_csv(STAGE_2_DATA / "industry/baseyear_industry_demand.csv"),
                pd.read_csv(
                    STAGE_4_DATA / "subres_ind/future_industry_process_definitions.csv"
                ),
                pd.read_csv(REPORTING_ASSUMPTIONS / "industry_demand_overrides.csv"),
            ),
            build_residential_processes(
                pd.read_csv(
                    STAGE_2_DATA / "residential/baseyear_residential_demand.csv"
                )
            ),
            build_commercial_processes(
                pd.read_csv(STAGE_2_DATA / "commercial/baseyear_commercial_demand.csv"),
                pd.read_csv(
                    STAGE_4_DATA
                    / "subres_com/future_commercial_process_definitions.csv"
                ),
                pd.read_csv(REPORTING_ASSUMPTIONS / "commercial_demand_overrides.csv"),
            ),
            build_agriculture_processes(
                pd.read_csv(
                    STAGE_2_DATA / "ag_forest_fish/baseyear_ag_forest_fish_demand.csv"
                ),
                pd.read_csv(
                    STAGE_4_DATA
                    / "subres_agr/future_agriculture_process_definitions.csv"
                ),
            ),
            build_transport_processes(
                pd.read_csv(STAGE_4_DATA / "base_year_tra/tra_process_parameters.csv"),
                pd.read_csv(
                    STAGE_4_DATA
                    / "subres_tra/future_transport_details_advanced_costcurve.csv"
                ),
                pd.read_csv(REPORTING_ASSUMPTIONS / "transport_demand_commodities.csv"),
                pd.read_csv(REPORTING_ASSUMPTIONS / "transport_technology_labels.csv"),
            ),
        ]
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    processes.to_csv(OUTPUT_DIR / "demand_processes.csv", index=False)
    build_demand_commodities(processes).to_csv(
        OUTPUT_DIR / "demand_commodities.csv", index=False
    )


if __name__ == "__main__":
    main()
