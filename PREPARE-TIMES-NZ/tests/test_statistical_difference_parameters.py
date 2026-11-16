import pandas as pd
from prepare_times_nz.stage_4.electricity.statistical_difference import (
    create_statistical_difference_parameters,
)


def test_statistical_difference_uses_configured_share_and_carries_forward():
    source = pd.DataFrame(
        {
            "Year": [2022, 2023, 2024],
            "CalculatedDemandGWh": [200.0, 1600.0, 2000.0],
            "ObservedDemandGWh": [100.0, 1000.0, 1000.0],
        }
    )

    baseyear_demand_tables = [
        pd.DataFrame(
            {
                "Region": ["NI", "SI"],
                "Fuel": ["Electricity", "Electricity"],
                "Variable": ["InputEnergy", "InputEnergy"],
                "Value": [3.0, 1.0],
            }
        )
    ]

    result = create_statistical_difference_parameters(
        source, baseyear_demand_tables, 0.8, 2023
    )

    assert result.to_dict("records") == [
        {
            "TechName": "StatDiffDemand_ELC",
            "Comm-IN": "ELC",
            "Region": "NI",
            "ACT_BND~FX~2023": 1.296,
            "ACT_BND~FX~2024": 2.16,
            "ACT_BND~FX~0": 5,
        },
        {
            "TechName": "StatDiffDemand_ELC",
            "Comm-IN": "ELC",
            "Region": "SI",
            "ACT_BND~FX~2023": 0.432,
            "ACT_BND~FX~2024": 0.72,
            "ACT_BND~FX~0": 5,
        },
    ]
