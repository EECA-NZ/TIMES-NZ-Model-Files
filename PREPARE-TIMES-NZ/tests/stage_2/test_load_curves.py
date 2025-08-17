import numpy as np
import pandas as pd
from prepare_times_nz.stage_2 import load_curves as lc

BASE_YEAR = 2023


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


def write_island_concordance(tmp_path):
    path = tmp_path / "nsp_concordance.csv"
    pd.DataFrame(
        {"POC": ["ABC", "DEF", "123"], "Island": ["North", "South", "Chatham"]}
    ).to_csv(path, index=False)
    return str(path)


def test_add_islands_basic(tmp_path):
    nsp_file = write_island_concordance(tmp_path)

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
    nsp_file = write_island_concordance(tmp_path)

    df_in = pd.DataFrame({"POC": [123456]})
    out = lc.add_islands(df_in, nsp_file=nsp_file)

    assert list(out.columns) == ["POC", "Island"]
    assert out.loc[0, "Island"] == "Chatham"


def test_summary_timeslice_with_island(tmp_path):

    fake_input = pd.DataFrame(
        {
            "Year": [2024, 2024, 2024],
            "TimeSlice": ["Peak", "Peak", "Peak"],
            "Trading_Date": [pd.Timestamp("2024-01-01")] * 3,
            "Hour": [1, 2, 1],
            "Unit_Measure": ["kWh", "kWh", "kWh"],
            "POC": ["ABC001", "ABC001", "DEF999"],
            "Value": [100_000, 200_000, 300_000],  # kWh
        }
    )

    nsp_file = write_island_concordance(tmp_path)
    out = lc.get_summary_timeslices(fake_input, by_island=True, nsp_file=nsp_file)

    # North: 100k + 200k = 300k kWh = 0.3 GWh over 2 hours -> 0.15 GW
    # South: 300k kWh = 0.3 GWh over 1 hour -> 0.3 GW
    exp = (
        pd.DataFrame(
            {
                "Year": [2024, 2024],
                "TimeSlice": ["Peak", "Peak"],
                "Unit_Measure": ["GWh", "GWh"],
                "Island": ["North", "South"],
                "Value": [0.3, 0.3],
                "HoursInSlice": [2, 1],
                "AverageLoadGW": [0.15, 0.3],
            }
        )
        .sort_values(["Island"])
        .reset_index(drop=True)
    )

    out = out.sort_values(["Island"]).reset_index(drop=True)
    pd.testing.assert_series_equal(
        out["Unit_Measure"], exp["Unit_Measure"], check_names=False
    )
    pd.testing.assert_series_equal(out["Island"], exp["Island"], check_names=False)
    pd.testing.assert_series_equal(
        out["HoursInSlice"], exp["HoursInSlice"], check_names=False
    )
    assert np.allclose(out["Value"], exp["Value"])
    assert np.allclose(out["AverageLoadGW"], exp["AverageLoadGW"])


def get_base_year_test_input():
    return pd.DataFrame(
        {
            "Year": [BASE_YEAR, BASE_YEAR, BASE_YEAR - 1],
            "Value": [100.0, 300.0, 999.0],
            "Other": [1, 2, 3],
        }
    )


def test_base_year_basic():
    df_in = get_base_year_test_input()
    out = lc.get_base_year_load_curves(df_in, base_year=BASE_YEAR)

    # only BASE_YEAR rows remain
    assert (out["Year"] == BASE_YEAR).all()
    assert len(out) == 2

    # 100/400 and 300/400
    assert np.isclose(out["LoadCurve"].sum(), 1.0)
    np.testing.assert_allclose(out["LoadCurve"].to_numpy(), [0.25, 0.75], atol=1e-12)

    # input not mutated
    assert "LoadCurve" not in df_in.columns


def test_zero_total_ok():
    df_zero = pd.DataFrame({"Year": [BASE_YEAR, BASE_YEAR], "Value": [0.0, 0.0]})
    out = lc.get_base_year_load_curves(df_zero, base_year=BASE_YEAR)
    assert len(out) == 2
    assert out["LoadCurve"].isna().all()


def test_no_matching_rows():
    df_in = get_base_year_test_input()
    out = lc.get_base_year_load_curves(df_in, base_year=BASE_YEAR + 100)
    assert out.empty
    assert "LoadCurve" in out.columns


# get_yrfr() -------------------------------------------------------------------


def make_yrfr_test_input(base_year, hours_peak, hours_offpeak):
    """Minimal DF that get_base_year_load_curves will accept and keep HoursInSlice."""
    return pd.DataFrame(
        {
            "Year": [base_year, base_year],
            "TimeSlice": ["Peak", "Offpeak"],
            "HoursInSlice": [hours_peak, hours_offpeak],
            # Value is required by get_base_year_load_curves but not used by get_yrfr logic
            "Value": [1.0, 1.0],
        }
    )


def test_yrfr_normal_year_no_warning(caplog):

    base_year = BASE_YEAR

    # 2000 + 6760 = 8760
    df_in = make_yrfr_test_input(base_year, 2000, 6760)
    with caplog.at_level("WARNING"):
        out = lc.get_yrfr(df_in)

    # Output columns + shape
    assert list(out.columns) == ["TimeSlice", "YRFR"]
    assert len(out) == 2

    # YRFR per slice: hours / 8760
    out_sorted = out.sort_values("TimeSlice").reset_index(drop=True)
    expected = pd.Series([2000 / 8760, 6760 / 8760], name="YRFR").sort_values(
        ignore_index=True
    )
    assert np.isclose(out_sorted["YRFR"].sum(), 1.0)
    np.testing.assert_allclose(
        sorted(out_sorted["YRFR"].to_list()),
        sorted(expected.to_list()),
        atol=1e-12,
    )

    # No warnings for exactly 8760
    assert "incorrect number of hours" not in caplog.text
    assert "leap year" not in caplog.text


def test_yrfr_leap_year_warns(caplog):

    base_year = BASE_YEAR

    # 2000 + 6784 = 8784
    df_in = make_yrfr_test_input(base_year, 2000, 6784)
    with caplog.at_level("WARNING"):
        out = lc.get_yrfr(df_in)

    # Still sums to 1 across YRFRs
    assert np.isclose(out["YRFR"].sum(), 1.0)

    # Warns about leap-year length
    assert "leap year" in caplog.text.lower()
    assert "8784" in caplog.text


def test_yrfr_incorrect_hours_warns(caplog):
    base_year = BASE_YEAR

    # 8750 total -> not 8760/8784
    df_in = make_yrfr_test_input(base_year, 2000, 6750)
    with caplog.at_level("WARNING"):
        out = lc.get_yrfr(df_in)

    # YRFR still computed (just won’t sum to 1 if you summed HoursInSlice directly),
    # but within this function it *will* sum to 1 because YRFR uses HoursInYear as denominator.
    assert np.isclose(out["YRFR"].sum(), 1.0)

    # Warns about incorrect number of hours
    text = caplog.text.lower()
    assert "incorrect number of hours" in text
    assert "8750" in text


# get_residential_curves() ---------------------------------


def get_fake_res_curve_input(base_year):
    # ABC001 and DEF999 are “residential”; GHI000 is not
    return pd.DataFrame(
        {
            "Year": [base_year, base_year, base_year, base_year - 1],
            "TimeSlice": ["Peak", "Offpeak", "Peak", "Peak"],
            "Unit_Measure": ["kWh", "kWh", "kWh", "kWh"],
            "POC": ["ABC001", "ABC001", "DEF999", "ABC001"],
            "Value": [100.0, 300.0, 200.0, 999.0],
        }
    )


def test_without_islands_basic():
    base_year = BASE_YEAR
    df_in = get_fake_res_curve_input(base_year)

    out = lc.get_residential_curves(
        df_in,
        with_islands=False,
        base_year=base_year,
        residential_pocs=["ABC001", "DEF999"],
    )

    # Should aggregate over POCs within each timeslice for the base year only.
    # Totals: Peak = 100 + 200 = 300, Offpeak = 300, sum = 600
    # LoadCurve: Peak = 300/600 = 0.5, Offpeak = 300/600 = 0.5
    assert list(out.columns) == ["Year", "TimeSlice", "LoadCurve"]
    assert (out["Year"] == base_year).all()
    assert set(out["TimeSlice"]) == {"Peak", "Offpeak"}
    assert np.isclose(out["LoadCurve"].sum(), 1.0)
    # Map for easy checks
    lc_map = dict(zip(out["TimeSlice"], out["LoadCurve"]))
    assert np.isclose(lc_map["Peak"], 0.5)
    assert np.isclose(lc_map["Offpeak"], 0.5)


def test_with_islands_basic(tmp_path):

    base_year = BASE_YEAR
    df_in = get_fake_res_curve_input(base_year)
    nsp_file = write_island_concordance(tmp_path)

    out = lc.get_residential_curves(
        df_in,
        with_islands=True,
        base_year=base_year,
        residential_pocs=["ABC001", "DEF999"],
        nsp_file=nsp_file,
    )

    # After filtering: base year + residential POCs
    # Rows (with islands):
    #   Peak/North: 100
    #   Peak/South: 200
    #   Offpeak/North: 300
    # Total = 600 -> LoadCurve values: 100/600, 200/600, 300/600
    assert set(out.columns) == {"Year", "TimeSlice", "Island", "LoadCurve"}
    assert len(out) == 3
    assert np.isclose(out["LoadCurve"].sum(), 1.0)

    # Build a checkable key
    out_keyed = {
        (r.TimeSlice, r.Island): r.LoadCurve for r in out.itertuples(index=False)
    }
    assert np.isclose(out_keyed[("Peak", "North")], 100.0 / 600.0)
    assert np.isclose(out_keyed[("Peak", "South")], 200.0 / 600.0)
    assert np.isclose(out_keyed[("Offpeak", "North")], 300.0 / 600.0)


def test_empty_after_filter():

    base_year = BASE_YEAR

    # No residential POCs match -> empty after filtering
    df_in = get_fake_res_curve_input(base_year)
    out = lc.get_residential_curves(
        df_in,
        with_islands=False,
        base_year=base_year,
        residential_pocs=["NOTHING"],
    )

    # Should be empty but with expected columns
    assert out.empty
    assert list(out.columns) == ["Year", "TimeSlice", "LoadCurve"]
