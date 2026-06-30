"""
Build all analysis charts by running each subject-area chart module.

Initial data cleaning and aggregating is performed in analysis.get_data. Shared
plotting helpers live in analysis_chart_helpers, while each subject module owns
the charts for that subject area.
"""

from times_nz_internal_qa.analysis import (
    analysis_demand,
    analysis_electricity_generation,
    analysis_emissions,
    analysis_indicators,
    analysis_primary_energy,
    analysis_transport,
)

ANALYSIS_CHART_MODULES = [
    analysis_indicators,
    analysis_electricity_generation,
    analysis_emissions,
    analysis_primary_energy,
    analysis_demand,
    analysis_transport,
]


def main():
    """Run every subject-area chart module."""

    for chart_module in ANALYSIS_CHART_MODULES:
        chart_module.main()


if __name__ == "__main__":
    main()
