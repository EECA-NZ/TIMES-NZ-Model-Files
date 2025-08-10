import importlib

import numpy as np
import pandas as pd
from prepare_times_nz.stage_2 import load_curves as lc


def test_aggregate_emi_by_timeslice_groups_and_filters():
    # Fake input
    df = pd.DataFrame(
        {
            "Trading_Date": [
                pd.Timestamp("2023-01-01"),
                pd.Timestamp("2023-01-01"),
                pd.Timestamp("2023-03-26"),
                pd.Timestamp("2023-03-26"),
                pd.Timestamp("2023-03-26"),
            ],
            "TimeSlice": ["SUM-WK-D", "SUM-WK-D", "SUM-WK-N", "SUM-WK-N", "SUM-WK-P"],
            "POC": ["POC1", "POC1", "POC2", "POC2", "POC3"],
            "Hour": [1, 1, 24, 24, 2],
            "Unit_Measure": ["kWh"] * 5,
            "Value": [10.0, 5.0, 7.0, 3.0, 4.0],
        }
    )

    # Act
    out = lc.aggregate_emi_by_timeslice(df)

    # Assert
    expected = pd.DataFrame(
        {
            "Year": [2023, 2023],
            "TimeSlice": ["SUM-WK-D", "SUM-WK-P"],
            "POC": ["POC1", "POC3"],
            "Trading_Date": [pd.Timestamp("2023-01-01"), pd.Timestamp("2023-03-26")],
            "Hour": [1, 2],
            "Unit_Measure": ["kWh", "kWh"],
            "Value": [15.0, 4.0],
        }
    )

    sort_cols = ["Year", "TimeSlice", "POC", "Trading_Date", "Hour", "Unit_Measure"]
    pd.testing.assert_frame_equal(
        out.sort_values(sort_cols).reset_index(drop=True),
        expected.sort_values(sort_cols).reset_index(drop=True),
    )


def write_concordance(tmp_path):
    path = tmp_path / "nsp_concordance.csv"
    pd.DataFrame(
        {"POC": ["ABC", "DEF", "123"], "Island": ["North", "South", "Chatham"]}
    ).to_csv(path, index=False)
    return str(path)


def test_add_islands_basic(tmp_path):
    nsp_file = write_concordance(tmp_path)

    df_in = pd.DataFrame(
        {"POC": ["ABC12345", "DEF999", "GHI000"], "OtherCol": [1, 2, 3]}
    )
    out = lc.add_islands(df_in, nsp_file=nsp_file)

    expected = pd.DataFrame(
        {
            "POC": ["ABC12345", "DEF999", "GHI000"],
            "OtherCol": [1, 2, 3],
            "Island": ["North", "South", np.nan],
        }
    )
    pd.testing.assert_frame_equal(out.reset_index(drop=True), expected)


def test_add_islands_numeric_poc(tmp_path):
    nsp_file = write_concordance(tmp_path)

    df_in = pd.DataFrame({"POC": [123456]})
    out = lc.add_islands(df_in, nsp_file=nsp_file)

    assert list(out.columns) == ["POC", "Island"]
    assert out.loc[0, "Island"] == "Chatham"
