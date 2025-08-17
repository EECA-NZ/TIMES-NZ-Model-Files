import numpy as np
import pandas as pd
import pytest
from prepare_times_nz.stage_2 import disaggregate_residential_demand as rd

BASE_YEAR = 2023


def write_test_data_to_temp(df, tmp_path, file_name):
    """
    Just for taking test data and writing to fake locations
    Can use for test I/Os
    """

    path = tmp_path / file_name
    df.to_csv(path, index=False)
    return str(path)


def test_get_population_data_filters_by_base_year(tmp_path):
    # Arrange: create test DataFrame with multiple years
    test_df = pd.DataFrame(
        {
            "CensusYear": [2023, 2023, 2021, 2022],
            "Region": ["Auckland", "Wellington", "Auckland", "Canterbury"],
            "DwellingType": ["House", "Apartment", "House", "Apartment"],
            "Population": [1000, 2000, 1500, 1800],
        }
    )

    # Write the test data to a temp CSV using provided helper
    filepath = write_test_data_to_temp(test_df, tmp_path, "test_pop.csv")

    # Act: call the function under test
    filtered_df = rd.get_population_data(filepath=filepath, base_year=BASE_YEAR)

    # Assert: only rows from BASE_YEAR (2023) should be returned
    assert not filtered_df.empty, "Expected non-empty DataFrame for BASE_YEAR"
    assert all(
        filtered_df["CensusYear"] == BASE_YEAR
    ), "All rows should match BASE_YEAR"
    assert len(filtered_df) == 2, "Expected exactly 2 rows for BASE_YEAR"

    # Also check that the content matches expected subset
    expected_regions = {"Auckland", "Wellington"}
    assert (
        set(filtered_df["Region"]) == expected_regions
    ), "Unexpected regions in filtered data"


def test_get_population_shares_basic():
    raw = pd.DataFrame(
        {
            "Area": ["Auckland", "Wellington", "Canterbury"],
            "DwellingType": ["Detached", "Detached", "Joined"],
            "Value": [50, 30, 20],
        }
    )

    result = rd.get_population_shares(raw)

    # Columns match expected
    assert list(result.columns) == ["Area", "DwellingType", "ShareOfPopulation"]

    # Shares sum to 1
    assert np.isclose(result["ShareOfPopulation"].sum(), 1.0, atol=1e-8)

    # Expected shares
    expected_shares = [0.5, 0.3, 0.2]
    np.testing.assert_allclose(result["ShareOfPopulation"].values, expected_shares)


def test_get_population_shares_multiple_dwelling_types():
    raw = pd.DataFrame(
        {
            "Area": ["Auckland", "Auckland", "Canterbury", "Canterbury"],
            "DwellingType": ["Detached", "Joined", "Detached", "Joined"],
            "Value": [60, 40, 30, 30],
        }
    )

    result = rd.get_population_shares(raw)

    # Shares sum to 1
    assert np.isclose(result["ShareOfPopulation"].sum(), 1.0)

    # Auckland Detached share should be 60/160 = 0.375
    ak_det_share = result.loc[
        (result["Area"] == "Auckland") & (result["DwellingType"] == "Detached"),
        "ShareOfPopulation",
    ].item()
    assert np.isclose(ak_det_share, 0.375, atol=1e-8)


def test_get_population_shares_with_zero_values():
    raw = pd.DataFrame(
        {
            "Area": ["Auckland", "Wellington"],
            "DwellingType": ["Detached", "Joined"],
            "Value": [0, 0],
        }
    )

    # This will produce NaN shares; check it doesn't crash
    result = rd.get_population_shares(raw)
    assert result["ShareOfPopulation"].isna().all()


def test_get_population_shares_does_not_mutate_input():
    raw = pd.DataFrame(
        {
            "Area": ["Auckland"],
            "DwellingType": ["Detached"],
            "Value": [100],
        }
    )
    raw_copy = raw.copy(deep=True)

    _ = rd.get_population_shares(raw)

    pd.testing.assert_frame_equal(raw, raw_copy)


@pytest.mark.parametrize("missing_col", ["Area", "DwellingType", "Value"])
def test_get_population_shares_raises_key_error_on_missing_columns(missing_col):
    df = pd.DataFrame(
        {
            "Area": ["Auckland"],
            "DwellingType": ["Detached"],
            "Value": [100],
        }
    ).drop(columns=[missing_col])

    with pytest.raises(KeyError, match="Missing required column"):
        rd.get_population_shares(df)


def test_clean_population_data_excludes_and_tidy_areas():
    raw = pd.DataFrame(
        {
            "Area": [
                "Auckland Region",
                "Canterbury Region",
                "Area Outside Region",
                "Total - New Zealand by regional council",
            ],
            "DwellingType": [
                "Separate house",
                "Joined dwelling",
                "Separate house",
                "Joined dwelling",
            ],
            "CensusYear": [2023, 2023, 2023, 2023],
            "Value": [100, 50, 999, 999],
        }
    )

    out = rd.clean_population_data(raw)

    # Excluded regions should be gone
    assert not (
        out["Area"].isin(
            ["Area Outside Region", "Total - New Zealand by regional council"]
        )
    ).any()

    # Suffix " Region" removed
    assert set(out["Area"]) == {"Auckland", "Canterbury"}


def test_clean_population_data_maps_and_aggregates_values():
    # Two Auckland rows of "Separate house" should map to "Detached" and sum
    # Two Canterbury rows of "Joined dwelling" should map to "Joined" and sum
    raw = pd.DataFrame(
        {
            "Area": [
                "Auckland Region",
                "Auckland Region",
                "Canterbury Region",
                "Canterbury Region",
            ],
            "DwellingType": [
                "Separate house",
                "Private dwelling not further defined",
                "Joined dwelling",
                "Joined dwelling",
            ],
            "CensusYear": [2023, 2023, 2023, 2023],
            "Sex": ["Total", "Total", "Total", "Total"],
            "Value": [10, 5, 7, 8],
        }
    )

    out = rd.clean_population_data(raw)

    expected = pd.DataFrame(
        {
            "Area": ["Auckland", "Canterbury"],
            "DwellingType": ["Detached", "Joined"],
            "CensusYear": [2023, 2023],
            "Sex": ["Total", "Total"],
            "Value": [15, 15],
        }
    )

    # Sort for stable comparison and reset index
    out_sorted = out.sort_values(["Area", "DwellingType"]).reset_index(drop=True)
    expected_sorted = expected.sort_values(["Area", "DwellingType"]).reset_index(
        drop=True
    )

    pd.testing.assert_frame_equal(out_sorted, expected_sorted)


def test_returns_base_year_when_present():
    df = pd.DataFrame({"CensusYear": [2021, 2023, 2023], "Value": [1, 2, 3]})

    result = rd.get_latest_census_year(df, base_year=2023)

    assert set(result["CensusYear"]) == {2023}
    assert len(result) == 2
    assert result["Value"].tolist() == [2, 3]


def test_returns_latest_year_when_base_missing():
    df = pd.DataFrame({"CensusYear": [2018, 2021, 2021], "Value": [1, 2, 3]})

    result = rd.get_latest_census_year(df, base_year=2023)

    assert set(result["CensusYear"]) == {2021}
    assert len(result) == 2
    assert result["Value"].tolist() == [2, 3]


def test_clean_census_data_happy_path_and_suffix_strip():
    raw = pd.DataFrame(
        {
            "MainTypesOfHeatingUsed": ["Electric heater", "Heat pump"],
            "PrivateDwellingType": ["Separate house", "Joined dwelling"],
            "Area": ["Auckland Region", "Canterbury Region"],
            "Value": [10, 20],
        }
    )

    out = rd.clean_census_data(raw)

    # Columns renamed
    assert "HeatingType" in out.columns
    assert "DwellingType" in out.columns
    assert "MainTypesOfHeatingUsed" not in out.columns
    assert "PrivateDwellingType" not in out.columns

    # Area suffix removed
    assert set(out["Area"]) == {"Auckland", "Canterbury"}

    # Other columns preserved
    pd.testing.assert_series_equal(
        out["Value"].reset_index(drop=True), pd.Series([10, 20], name="Value")
    )


def test_clean_census_data_excludes_regions():
    raw = pd.DataFrame(
        {
            "MainTypesOfHeatingUsed": ["Electric heater", "Heat pump", "Wood burner"],
            "PrivateDwellingType": [
                "Separate house",
                "Joined dwelling",
                "Separate house",
            ],
            "Area": [
                "Area Outside Region",
                "Total - New Zealand by regional council",
                "Wellington Region",
            ],
            "Value": [999, 999, 5],
        }
    )

    out = rd.clean_census_data(raw)

    # Only Wellington should remain, and suffix stripped
    assert len(out) == 1
    row = out.iloc[0]
    assert row["Area"] == "Wellington"
    assert row["HeatingType"] == "Wood burner"
    assert row["DwellingType"] == "Separate house"
    assert row["Value"] == 5


@pytest.mark.parametrize(
    "missing_col",
    [
        "MainTypesOfHeatingUsed",
        "PrivateDwellingType",
        "Area",
    ],
)
def test_clean_census_data_raises_on_missing_columns(missing_col):
    cols = {
        "MainTypesOfHeatingUsed": ["Heat pump"],
        "PrivateDwellingType": ["Separate house"],
        "Area": ["Auckland Region"],
        "Value": [1],
    }
    cols.pop(missing_col)
    raw = pd.DataFrame(cols)

    with pytest.raises(KeyError, match="Missing required column"):
        rd.clean_census_data(raw)


def test_clean_census_data_does_not_mutate_input():
    raw = pd.DataFrame(
        {
            "MainTypesOfHeatingUsed": ["Heat pump"],
            "PrivateDwellingType": ["Separate house"],
            "Area": ["Auckland Region"],
            "Value": [1],
        }
    )
    raw_copy = raw.copy(deep=True)

    _ = rd.clean_census_data(raw)

    pd.testing.assert_frame_equal(raw, raw_copy)


def test_aggregate_dwelling_types_basic_aggregation():
    raw = pd.DataFrame(
        {
            "DwellingType": [
                "Separate house",
                "Joined dwelling",
                "Private dwelling not further defined",
                "Total - private dwelling type",
            ],
            "Area": ["Auckland", "Auckland", "Wellington", "Wellington"],
            "Value": [10, 5, 20, 35],
        }
    )

    result = rd.aggregate_dwelling_types(raw, run_tests=False)

    # Only Detached & Joined remain
    assert set(result["DwellingType"]) == {"Detached", "Joined"}
    # Check aggregation correctness
    expected = pd.DataFrame(
        {
            "DwellingType": ["Detached", "Joined", "Detached"],
            "Area": ["Auckland", "Auckland", "Wellington"],
            "Value": [10, 5, 20],
        }
    )
    pd.testing.assert_frame_equal(
        result.sort_values(result.columns.tolist()).reset_index(drop=True),
        expected.sort_values(expected.columns.tolist()).reset_index(drop=True),
    )


def test_aggregate_dwelling_types_run_tests_keeps_total():
    raw = pd.DataFrame(
        {
            "DwellingType": [
                "Separate house",
                "Joined dwelling",
                "Total - private dwelling type",
            ],
            "Area": ["Auckland", "Auckland", "Auckland"],
            "Value": [10, 5, 15],
        }
    )

    result = rd.aggregate_dwelling_types(raw, run_tests=True)

    # All three categories should remain
    assert set(result["DwellingType"]) == {"Detached", "Joined", "Total"}
    # Totals match expectations
    total_row = result.loc[result["DwellingType"] == "Total", "Value"].item()
    assert total_row == 15


def test_aggregate_dwelling_types_missing_column_raises():
    raw = pd.DataFrame(
        {
            "DwellingType": ["Separate house"],
            "Area": ["Auckland"],
            # Missing 'Value'
        }
    )

    with pytest.raises(KeyError, match="Missing required column"):
        rd.aggregate_dwelling_types(raw)


def test_aggregate_dwelling_types_sums_values_for_same_group():
    raw = pd.DataFrame(
        {
            "DwellingType": [
                "Separate house",
                "Separate house",
                "Joined dwelling",
                "Joined dwelling",
            ],
            "Area": ["Auckland", "Auckland", "Auckland", "Auckland"],
            "Value": [5, 5, 2, 3],
        }
    )

    result = rd.aggregate_dwelling_types(raw, run_tests=False)

    # Detached sum = 10, Joined sum = 5
    det_val = result.loc[result["DwellingType"] == "Detached", "Value"].item()
    joined_val = result.loc[result["DwellingType"] == "Joined", "Value"].item()
    assert det_val == 10
    assert joined_val == 5


def test_get_dwelling_heating_data_end_to_end(tmp_path):
    # Raw census-like data across years; one excluded region
    raw = pd.DataFrame(
        {
            "CensusYear": [2023, 2023, 2023],
            "Area": ["Auckland Region", "Canterbury Region", "Area Outside Region"],
            "PrivateDwellingType": [
                "Separate house",
                "Joined dwelling",
                "Separate house",
            ],
            "MainTypesOfHeatingUsed": ["Heat pump", "Electric heater", "Heat pump"],
            "Value": [10, 5, 999],
        }
    )
    csv_path = tmp_path / "dwelling_heating.csv"
    raw.to_csv(csv_path, index=False)

    result = rd.get_dwelling_heating_data(
        run_tests=False,
        dwelling_heating_file=str(csv_path),
    )

    # Required columns present
    required_cols = {"CensusYear", "Area", "DwellingType", "HeatingType", "Value"}
    assert required_cols.issubset(result.columns)

    # Excluded region removed; " Region" suffix stripped
    assert set(result["Area"]) == {"Auckland", "Canterbury"}

    # Dwelling types aggregated (no "Total" when run_tests=False)
    assert set(result["DwellingType"]) == {"Detached", "Joined"}

    # Values aggregated correctly
    ak_det = result.loc[
        (result["Area"] == "Auckland")
        & (result["DwellingType"] == "Detached")
        & (result["HeatingType"] == "Heat pump"),
        "Value",
    ].item()
    assert ak_det == 10

    can_join = result.loc[
        (result["Area"] == "Canterbury")
        & (result["DwellingType"] == "Joined")
        & (result["HeatingType"] == "Electric heater"),
        "Value",
    ].item()
    assert can_join == 5


def test_get_dwelling_heating_data_run_tests_true_keeps_total(tmp_path):
    # Include an explicit "Total - private dwelling type" row to be preserved
    raw = pd.DataFrame(
        {
            "CensusYear": [2023, 2023, 2023],
            "Area": ["Auckland Region", "Auckland Region", "Auckland Region"],
            "PrivateDwellingType": [
                "Separate house",
                "Joined dwelling",
                "Total - private dwelling type",
            ],
            "MainTypesOfHeatingUsed": ["Heat pump", "Heat pump", "Heat pump"],
            "Value": [10, 5, 15],
        }
    )
    csv_path = tmp_path / "dwelling_heating_totals.csv"
    raw.to_csv(csv_path, index=False)

    result = rd.get_dwelling_heating_data(
        run_tests=True,
        dwelling_heating_file=str(csv_path),
    )

    # When run_tests=True, the Total rows are kept by the aggregation step
    assert {"Detached", "Joined", "Total"} == set(result["DwellingType"])

    total_val = result.loc[
        (result["Area"] == "Auckland")
        & (result["DwellingType"] == "Total")
        & (result["HeatingType"] == "Heat pump"),
        "Value",
    ].item()
    assert total_val == 15


def test_get_total_dwellings_per_region_filters_and_renames():
    raw = pd.DataFrame(
        {
            "CensusYear": [2023, 2023, 2023],
            "Area": ["Auckland", "Wellington", "Canterbury"],
            "HeatingType": [
                "Total stated - main types of heating used",
                "Heat pump",
                "Total stated - main types of heating used",
            ],
            "Value": [100, 200, 300],
        }
    )

    result = rd.get_total_dwellings_per_region(raw)

    # Expected: only 2 rows remain
    expected = pd.DataFrame(
        {
            "CensusYear": [2023, 2023],
            "Area": ["Auckland", "Canterbury"],
            "TotalDwellingsInRegion": [100, 300],
        }
    )

    pd.testing.assert_frame_equal(
        result.sort_values(result.columns.tolist()).reset_index(drop=True),
        expected.sort_values(expected.columns.tolist()).reset_index(drop=True),
    )

    # HeatingType column should be removed
    assert "HeatingType" not in result.columns


@pytest.mark.parametrize("missing_col", ["HeatingType", "Value"])
def test_get_total_dwellings_per_region_missing_column_raises(missing_col):
    df = pd.DataFrame(
        {
            "CensusYear": [2023],
            "Area": ["Auckland"],
            "HeatingType": ["Total stated - main types of heating used"],
            "Value": [100],
        }
    )
    df = df.drop(columns=[missing_col])

    with pytest.raises(KeyError, match="Missing required column"):
        rd.get_total_dwellings_per_region(df)


def test_get_total_dwellings_per_region_excludes_non_total_rows():
    raw = pd.DataFrame(
        {
            "Area": ["Auckland", "Wellington"],
            "HeatingType": ["Heat pump", "Wood burner"],
            "Value": [50, 75],
        }
    )

    result = rd.get_total_dwellings_per_region(raw)

    # Should result in an empty DataFrame with renamed column
    assert result.empty
    assert "TotalDwellingsInRegion" in result.columns


def test_get_heating_shares_basic_and_sums_to_one():
    raw = pd.DataFrame(
        {
            "CensusYear": [2023, 2023, 2023, 2023, 2023, 2023],
            "Area": [
                "Auckland",
                "Auckland",
                "Auckland",
                "Wellington",
                "Wellington",
                "Wellington",
            ],
            "DwellingType": [
                "Detached",
                "Detached",
                "Detached",
                "Joined",
                "Joined",
                "Joined",
            ],
            "HeatingType": [
                "Heat pump",
                "Wood burner",
                "Total stated - main types of heating used",  # should be excluded
                "Heat pump",
                "Other types of heating",  # should be excluded
                "Wood burner",
            ],
            "Value": [60, 40, 100, 30, 999, 70],
        }
    )

    out = rd.get_heating_shares(raw, run_tests=True)

    # Excluded categories should be gone
    assert (
        not out["HeatingType"]
        .isin(
            [
                "Total stated - main types of heating used",
                "No heating used",
                "Other types of heating",
            ]
        )
        .any()
    )

    # Required columns present; Value/Total removed
    assert {
        "CensusYear",
        "Area",
        "DwellingType",
        "HeatingType",
        "FuelHeatingShare",
    } <= set(out.columns)
    assert "Value" not in out.columns
    assert "Total" not in out.columns

    # Shares are correctly computed
    # Auckland Detached: 60/100=0.6, 40/100=0.4
    ak = out[(out["Area"] == "Auckland") & (out["DwellingType"] == "Detached")]
    hp_share = ak.loc[ak["HeatingType"] == "Heat pump", "FuelHeatingShare"].item()
    wb_share = ak.loc[ak["HeatingType"] == "Wood burner", "FuelHeatingShare"].item()
    assert np.isclose(hp_share, 0.6)
    assert np.isclose(wb_share, 0.4)

    # Wellington Joined: only Heat pump (30) and Wood burner (70) counted; "Other types" excluded
    wel = out[(out["Area"] == "Wellington") & (out["DwellingType"] == "Joined")]
    shares_sum = wel["FuelHeatingShare"].sum()
    assert np.isclose(shares_sum, 1.0, atol=1e-8)


def test_get_heating_shares_does_not_mutate_input():
    raw = pd.DataFrame(
        {
            "CensusYear": [2023, 2023],
            "Area": ["Auckland", "Auckland"],
            "DwellingType": ["Detached", "Detached"],
            "HeatingType": ["Heat pump", "Wood burner"],
            "Value": [1, 1],
        }
    )
    raw_copy = raw.copy(deep=True)

    _ = rd.get_heating_shares(raw, run_tests=False)

    pd.testing.assert_frame_equal(raw, raw_copy)


@pytest.mark.parametrize(
    "missing_col", ["CensusYear", "Area", "DwellingType", "HeatingType", "Value"]
)
def test_get_heating_shares_raises_on_missing_columns(missing_col):
    df = pd.DataFrame(
        {
            "CensusYear": [2023],
            "Area": ["Auckland"],
            "DwellingType": ["Detached"],
            "HeatingType": ["Heat pump"],
            "Value": [10],
        }
    ).drop(columns=[missing_col])

    with pytest.raises(KeyError, match="Missing required column"):
        rd.get_heating_shares(df)


def test_add_islands_raises_when_island_missing_in_concordance(tmp_path):
    # Input needing an island join
    df = pd.DataFrame({"Area": ["Auckland"], "Value": [1]})

    # Concordance WITHOUT the 'Island' column -> should trigger KeyError
    bad_conc = pd.DataFrame(
        {
            "Region": ["Auckland"],
            # intentionally omit "Island"
        }
    )
    conc_path = tmp_path / "island_concordance.csv"
    bad_conc.to_csv(conc_path, index=False)

    with pytest.raises(KeyError, match="Merge failed to produce 'Island' column"):
        rd.add_islands(df, island_file=str(conc_path))


def test_add_assumptions_happy_path(tmp_path):
    base = pd.DataFrame(
        {
            "Area": ["Auckland", "Canterbury"],
            "DwellingType": ["Detached", "Joined"],
            "HeatingType": ["Heat pump", "Wood burner"],
            "FuelHeatingShare": [0.6, 0.4],
            "TotalDwellingsInRegion": [1000, 800],
        }
    )

    # Efficiency assumptions (merged on HeatingType); includes Note to be dropped
    eff_df = pd.DataFrame(
        {
            "HeatingType": ["Heat pump", "Wood burner"],
            "Technology": ["Heat pump", "Wood burner"],  # add
            "Fuel": ["Electricity", "Wood"],
            "EFF": [3.0, 0.75],
            "Note": ["hp note", "wb note"],
        }
    )
    eff_path = tmp_path / "eff.csv"
    eff_df.to_csv(eff_path, index=False)

    # Floor areas (left merge on DwellingType); includes Note to be dropped
    fa_df = pd.DataFrame(
        {
            "DwellingType": ["Detached", "Joined"],
            "FloorArea": [150.0, 95.0],
            "Note": ["fa1", "fa2"],
        }
    )
    fa_path = tmp_path / "fa.csv"
    fa_df.to_csv(fa_path, index=False)

    # HDD assumptions (Region,HDD -> rename Region->Area)
    hdd_df = pd.DataFrame(
        {
            "Region": ["Auckland", "Canterbury", "Wellington"],
            "HDD": [1200, 1800, 1600],
            "Extra": ["x", "y", "z"],
        }
    )
    hdd_path = tmp_path / "hdd.csv"
    hdd_df.to_csv(hdd_path, index=False)

    out = rd.add_assumptions(
        base,
        eff_assumptions=str(eff_path),
        floor_areas=str(fa_path),
        hdd_assumptions=str(hdd_path),
    )

    # Columns added; Note removed
    assert {"EFF", "FloorArea", "HDD"} <= set(out.columns)
    assert "Note" not in out.columns

    # Row count preserved
    assert len(out) == len(base)

    # Spot-check merged values
    hp_row = out.loc[out["HeatingType"] == "Heat pump"].iloc[0]
    assert hp_row["EFF"] == 3.0
    assert hp_row["FloorArea"] == 150.0
    assert hp_row["HDD"] == 1200

    wb_row = out.loc[out["HeatingType"] == "Wood burner"].iloc[0]
    assert wb_row["EFF"] == 0.75
    assert wb_row["FloorArea"] == 95.0
    assert wb_row["HDD"] == 1800


@pytest.mark.parametrize("missing_col", ["Area", "DwellingType"])
def test_add_assumptions_raises_on_missing_required_cols(missing_col, tmp_path):
    base = pd.DataFrame(
        {
            "Area": ["Auckland"],
            "DwellingType": ["Detached"],
            "HeatingType": ["Heat pump"],
        }
    ).drop(columns=[missing_col])

    # Minimal valid CSVs (won’t be reached if error is raised early)
    pd.DataFrame({"HeatingType": ["Heat pump"], "EFF": [3.0], "Note": ["n"]}).to_csv(
        tmp_path / "eff.csv", index=False
    )
    pd.DataFrame(
        {"DwellingType": ["Detached"], "FloorArea": [100.0], "Note": ["n"]}
    ).to_csv(tmp_path / "fa.csv", index=False)
    pd.DataFrame({"Region": ["Auckland"], "HDD": [1200]}).to_csv(
        tmp_path / "hdd.csv", index=False
    )

    with pytest.raises(KeyError, match="Missing required column"):
        rd.add_assumptions(
            base,
            eff_assumptions=str(tmp_path / "eff.csv"),
            floor_areas=str(tmp_path / "fa.csv"),
            hdd_assumptions=str(tmp_path / "hdd.csv"),
        )


def test_add_assumptions_does_not_mutate_input(tmp_path):
    base = pd.DataFrame(
        {
            "Area": ["Auckland"],
            "DwellingType": ["Detached"],
            "HeatingType": ["Heat pump"],
            "FuelHeatingShare": [0.6],
        }
    )
    base_copy = base.copy(deep=True)

    pd.DataFrame(
        {
            "HeatingType": ["Heat pump"],
            "Technology": ["Heat pump"],
            "Fuel": ["Electricity"],
            "EFF": [3.2],
            "Note": ["n"],
        }
    ).to_csv(tmp_path / "eff.csv", index=False)
    pd.DataFrame(
        {"DwellingType": ["Detached"], "FloorArea": [145.0], "Note": ["n"]}
    ).to_csv(tmp_path / "fa.csv", index=False)
    pd.DataFrame({"Region": ["Auckland"], "HDD": [1250], "Other": ["x"]}).to_csv(
        tmp_path / "hdd.csv", index=False
    )

    _ = rd.add_assumptions(
        base,
        eff_assumptions=str(tmp_path / "eff.csv"),
        floor_areas=str(tmp_path / "fa.csv"),
        hdd_assumptions=str(tmp_path / "hdd.csv"),
    )

    pd.testing.assert_frame_equal(base, base_copy)


def test_add_assumptions_handles_missing_hdd_gracefully(tmp_path):
    base = pd.DataFrame(
        {
            "Area": ["Nonexistent"],
            "DwellingType": ["Detached"],
            "HeatingType": ["Heat pump"],
        }
    )

    pd.DataFrame(
        {
            "HeatingType": ["Heat pump"],
            "Technology": ["Heat pump"],
            "Fuel": ["Electricity"],
            "EFF": [3.2],
            "Note": ["n"],
        }
    ).to_csv(tmp_path / "eff.csv", index=False)
    pd.DataFrame(
        {"DwellingType": ["Detached"], "FloorArea": [150.0], "Note": ["n"]}
    ).to_csv(tmp_path / "fa.csv", index=False)
    # HDD does not include "Nonexistent" area → HDD should be NaN after left-merge
    pd.DataFrame({"Region": ["Auckland"], "HDD": [1200]}).to_csv(
        tmp_path / "hdd.csv", index=False
    )

    out = rd.add_assumptions(
        base,
        eff_assumptions=str(tmp_path / "eff.csv"),
        floor_areas=str(tmp_path / "fa.csv"),
        hdd_assumptions=str(tmp_path / "hdd.csv"),
    )

    assert "HDD" in out.columns
    assert pd.isna(out.loc[0, "HDD"])


def get_sh_model_test_input():
    # Two (Technology, Fuel) groups; simple numbers for clean arithmetic
    # EFF=1 to avoid extra fractions
    rows = [
        # Heat pump / Electricity (total input = 800 -> shares: A 0.75, B 0.25)
        dict(
            CensusYear=2023,
            Area="Auckland",
            DwellingType="Detached",
            Technology="Heat pump",
            Fuel="Electricity",
            TotalDwellingsInRegion=10,
            FloorArea=10,
            HDD=10,
            FuelHeatingShare=0.6,
            EFF=1.0,
        ),
        dict(
            CensusYear=2023,
            Area="Canterbury",
            DwellingType="Detached",
            Technology="Heat pump",
            Fuel="Electricity",
            TotalDwellingsInRegion=10,
            FloorArea=10,
            HDD=5,
            FuelHeatingShare=0.4,
            EFF=1.0,
        ),
        # Wood burner / Wood (total input = 1300 -> shares: A 100/1300, B 1200/1300)
        dict(
            CensusYear=2023,
            Area="Auckland",
            DwellingType="Detached",
            Technology="Wood burner",
            Fuel="Wood",
            TotalDwellingsInRegion=5,
            FloorArea=10,
            HDD=10,
            FuelHeatingShare=0.2,
            EFF=1.0,
        ),
        dict(
            CensusYear=2023,
            Area="Canterbury",
            DwellingType="Detached",
            Technology="Wood burner",
            Fuel="Wood",
            TotalDwellingsInRegion=15,
            FloorArea=10,
            HDD=10,
            FuelHeatingShare=0.8,
            EFF=1.0,
        ),
    ]
    return pd.DataFrame(rows)


def test_build_sh_model_basic_shares():
    df = get_sh_model_test_input()

    out = rd.build_sh_model(df)

    # Expected columns only
    expected_cols = {"Area", "DwellingType", "Technology", "Fuel", "FuelDemandShare"}
    assert set(out.columns) == expected_cols

    # Group-wise shares should sum to ~1 for each (year, tech, fuel)
    # (CensusYear is dropped in the output, so we group by the remaining keys)
    for tech, fuel in [("Heat pump", "Electricity"), ("Wood burner", "Wood")]:
        grp = out[(out["Technology"] == tech) & (out["Fuel"] == fuel)]
        s = grp["FuelDemandShare"].sum()
        assert np.isclose(s, 1.0, atol=1e-10)

    # Check specific shares (from the clean arithmetic above)
    hp = out[(out["Technology"] == "Heat pump") & (out["Fuel"] == "Electricity")]
    hp_ak = hp.loc[hp["Area"] == "Auckland", "FuelDemandShare"].item()
    hp_can = hp.loc[hp["Area"] == "Canterbury", "FuelDemandShare"].item()
    assert np.isclose(hp_ak, 0.75)
    assert np.isclose(hp_can, 0.25)

    wb = out[(out["Technology"] == "Wood burner") & (out["Fuel"] == "Wood")]
    wb_ak = wb.loc[wb["Area"] == "Auckland", "FuelDemandShare"].item()
    wb_can = wb.loc[wb["Area"] == "Canterbury", "FuelDemandShare"].item()
    # 100/1300 and 1200/1300
    assert np.isclose(wb_ak, 100 / 1300)
    assert np.isclose(wb_can, 1200 / 1300)


def test_build_sh_model_raises_when_required_columns_missing():
    # Missing EFF should cause a KeyError when the function accesses df["EFF"]
    df = pd.DataFrame(
        {
            "CensusYear": [2023],
            "Area": ["Auckland"],
            "DwellingType": ["Detached"],
            "Technology": ["Heat pump"],
            "Fuel": ["Electricity"],
            "TotalDwellingsInRegion": [10],
            "FloorArea": [10],
            "HDD": [10],
            "FuelHeatingShare": [0.6],
            # "EFF" missing
        }
    )

    with pytest.raises(KeyError):
        rd.build_sh_model(df)


def test_build_sh_model_does_not_mutate_input():
    df = pd.DataFrame(
        {
            "CensusYear": [2023],
            "Area": ["Auckland"],
            "DwellingType": ["Detached"],
            "Technology": ["Heat pump"],
            "Fuel": ["Electricity"],
            "TotalDwellingsInRegion": [10],
            "FloorArea": [10],
            "HDD": [10],
            "FuelHeatingShare": [0.6],
            "EFF": [1.0],
        }
    )
    df_copy = df.copy(deep=True)

    _ = rd.build_sh_model(df)

    pd.testing.assert_frame_equal(df, df_copy)


def test_get_eeud_space_heating_data_filters_and_aggregates(tmp_path):
    by = 2023  # explicit to exercise base_year param
    raw = pd.DataFrame(
        {
            "Year": [by, by, by, by, by - 1, by],
            "Sector": [
                "Residential",
                "Residential",
                "Residential",
                "Industrial",
                "Residential",
                "Residential",
            ],
            "EndUse": [
                "Low Temperature Heat (<100 C), Space Heating",  # keep
                "Low Temperature Heat (<100 C), Space Heating",  # keep
                "Low Temperature Heat (<100 C), Water Heating",  # drop (wrong enduse)
                "Low Temperature Heat (<100 C), Space Heating",  # drop (wrong sector)
                "Low Temperature Heat (<100 C), Space Heating",  # drop (wrong year)
                "Low Temperature Heat (<100 C), Space Heating",  # keep (Electricity)
            ],
            "Fuel": [
                "Natural Gas",
                "LPG",
                "Electricity",
                "Natural Gas",
                "LPG",
                "Electricity",
            ],
            "Region": [
                "A",
                "A",
                "A",
                "A",
                "A",
                "B",
            ],  # extra column to ensure groupby keeps dims
            "Value": [10, 5, 999, 123, 7, 20],
        }
    )
    p = tmp_path / "eeud.csv"
    raw.to_csv(p, index=False)

    out = rd.get_eeud_space_heating_data(eeud_file=str(p), base_year=by)

    # Only base-year Residential Space Heating rows remain
    assert set(out["Sector"]) == {"Residential"}
    assert set(out["EndUse"]) == {"Low Temperature Heat (<100 C), Space Heating"}
    assert set(out["Year"]) == {by}

    # NG+LPG collapsed to Gas/LPG, Electricity unchanged
    assert set(out["Fuel"]) == {"Gas/LPG", "Electricity"}

    # Values aggregated correctly per remaining dimensions (Region kept)
    gas_a = out.loc[(out["Fuel"] == "Gas/LPG") & (out["Region"] == "A"), "Value"].item()
    elec_b = out.loc[
        (out["Fuel"] == "Electricity") & (out["Region"] == "B"), "Value"
    ].item()
    assert gas_a == 15  # 10 (NG) + 5 (LPG)
    assert elec_b == 20  # base-year residential space heating/electricity in region B


def test_get_eeud_space_heating_data_returns_empty_when_no_matches(tmp_path):
    # Nothing matches (wrong sector and year)
    raw = pd.DataFrame(
        {
            "Year": [2022, 2022],
            "Sector": ["Industrial", "Industrial"],
            "EndUse": [
                "Low Temperature Heat (<100 C), Space Heating",
                "Low Temperature Heat (<100 C), Water Heating",
            ],
            "Fuel": ["Natural Gas", "Electricity"],
            "Value": [1, 2],
        }
    )
    p = tmp_path / "eeud_none.csv"
    raw.to_csv(p, index=False)

    out = rd.get_eeud_space_heating_data(eeud_file=str(p), base_year=2023)

    assert out.empty
    # Columns should still exist (groupby doesn’t run on empty pre-group state here)
    assert set(out.columns) == set(raw.columns)


def test_check_join_grain_mismatch_warns_and_prints_left(capsys, caplog):
    # df1 has an extra key (C,2023) not in df2
    df1 = pd.DataFrame(
        {"Area": ["A", "B", "C"], "Year": [2023, 2023, 2023], "v": [1, 2, 3]}
    )
    df2 = pd.DataFrame({"Area": ["A", "B"], "Year": [2023, 2023], "x": [10, 20]})

    with caplog.at_level("WARNING"):
        rd.check_join_grain(df1, df2, join_vars=["Area", "Year"])

    # One warning and printed diff showing the extra (C,2023)
    assert any("Grain mismatch found in join" in r.message for r in caplog.records)
    out = capsys.readouterr().out
    assert "C" in out and "2023" in out


def test_check_join_grain_mismatch_warns_and_prints_right(capsys, caplog):
    # df2 has an extra key (D,2023) not in df1
    df1 = pd.DataFrame({"Area": ["A", "B"], "Year": [2023, 2023], "v": [1, 2]})
    df2 = pd.DataFrame(
        {"Area": ["A", "B", "D"], "Year": [2023, 2023, 2023], "x": [10, 20, 30]}
    )

    with caplog.at_level("WARNING"):
        rd.check_join_grain(df1, df2, join_vars=["Area", "Year"])

    assert any("Grain mismatch found in join" in r.message for r in caplog.records)
    out = capsys.readouterr().out
    assert "D" in out and "2023" in out


def test_check_join_grain_mismatch_both_sides(capsys, caplog):
    # Extras on both sides to ensure both branches print
    df1 = pd.DataFrame({"Area": ["A", "X"], "Year": [2023, 2023], "v": [1, 9]})
    df2 = pd.DataFrame({"Area": ["A", "Y"], "Year": [2023, 2023], "x": [10, 99]})

    with caplog.at_level("WARNING"):
        rd.check_join_grain(df1, df2, join_vars=["Area", "Year"])

    assert any("Grain mismatch found in join" in r.message for r in caplog.records)
    out = capsys.readouterr().out
    # Both X and Y should be printed by the function
    assert "X" in out
    assert "Y" in out


def test_apply_sh_model_to_eeud_scales_values_and_drops_share(tmp_path):
    # Make a fake EEUD file
    eeud_df = pd.DataFrame(
        {
            "Year": [2023, 2023, 2023],
            "Sector": ["Residential", "Residential", "Residential"],
            "EndUse": ["Low Temperature Heat (<100 C), Space Heating"] * 3,
            "Region": ["A", "A", "B"],
            "Technology": ["Heat pump", "Wood burner", "Heat pump"],
            "Fuel": ["Electricity", "Wood", "Electricity"],
            "Value": [100.0, 50.0, 300.0],
        }
    )
    eeud_path = tmp_path / "eeud.csv"
    eeud_df.to_csv(eeud_path, index=False)

    # Model shares to apply
    shares = pd.DataFrame(
        {
            "Technology": ["Heat pump", "Wood burner"],
            "Fuel": ["Electricity", "Wood"],
            "FuelDemandShare": [0.25, 0.1],
        }
    )

    out = rd.apply_sh_model_to_eeud(
        shares,
        eeud_file=str(eeud_path),
        base_year=2023,
    )

    assert "FuelDemandShare" not in out.columns
    # Heat pump / Electricity: 100*0.25 = 25 (Region A), 300*0.25 = 75 (Region B)
    hp = out[(out["Technology"] == "Heat pump") & (out["Fuel"] == "Electricity")]
    assert np.isclose(hp.loc[hp["Region"] == "A", "Value"].item(), 25.0)
    assert np.isclose(hp.loc[hp["Region"] == "B", "Value"].item(), 75.0)
    # Wood burner / Wood: 50*0.1 = 5
    wb = out[(out["Technology"] == "Wood burner") & (out["Fuel"] == "Wood")]
    assert np.isclose(wb["Value"].item(), 5.0)


def test_apply_sh_model_to_eeud_handles_missing_share(tmp_path):
    eeud_df = pd.DataFrame(
        {
            "Year": [2023],
            "Sector": ["Residential"],
            "EndUse": ["Low Temperature Heat (<100 C), Space Heating"],
            "Region": ["A"],
            "Technology": ["Heat pump"],
            "Fuel": ["Electricity"],
            "Value": [100.0],
        }
    )
    eeud_path = tmp_path / "eeud.csv"
    eeud_df.to_csv(eeud_path, index=False)

    shares = pd.DataFrame(
        {
            "Technology": ["Wood burner"],
            "Fuel": ["Wood"],
            "FuelDemandShare": [0.5],
        }
    )

    out = rd.apply_sh_model_to_eeud(
        shares,
        eeud_file=str(eeud_path),
        base_year=2023,
    )

    # No match -> FuelDemandShare NaN -> Value becomes NaN
    assert pd.isna(out["Value"]).all()


def test_apply_sh_model_to_eeud_does_not_mutate_input(tmp_path):
    eeud_df = pd.DataFrame(
        {
            "Year": [2023],
            "Sector": ["Residential"],
            "EndUse": ["Low Temperature Heat (<100 C), Space Heating"],
            "Region": ["A"],
            "Technology": ["Heat pump"],
            "Fuel": ["Electricity"],
            "Value": [10.0],
        }
    )
    eeud_path = tmp_path / "eeud.csv"
    eeud_df.to_csv(eeud_path, index=False)

    shares = pd.DataFrame(
        {
            "Technology": ["Heat pump"],
            "Fuel": ["Electricity"],
            "FuelDemandShare": [0.2],
        }
    )
    shares_copy = shares.copy(deep=True)

    _ = rd.apply_sh_model_to_eeud(
        shares,
        eeud_file=str(eeud_path),
        base_year=2023,
    )

    pd.testing.assert_frame_equal(shares, shares_copy)


def _fuel_split(ng_value, lpg_value):
    total = ng_value + lpg_value
    return pd.DataFrame(
        {
            "Fuel": ["Natural Gas", "LPG"],
            "Value": [ng_value, lpg_value],
            "Share": [
                ng_value / total if total else np.nan,
                lpg_value / total if total else np.nan,
            ],
        }
    )


def _island_split(ni_value, si_value):
    total = ni_value + si_value
    return pd.DataFrame(
        {
            "Island": ["NI", "SI"],
            "Value": [ni_value, si_value],
            "Share": [
                ni_value / total if total else np.nan,
                si_value / total if total else np.nan,
            ],
        }
    )


def test_get_ni_lpg_share_happy_path_balanced():
    # EEUD fuel split: NG=60, LPG=40 → shares 0.6 and 0.4
    burner_fuel_split = _fuel_split(ng_value=60.0, lpg_value=40.0)
    # Island split (model): NI total 90, SI total 10 → shares 0.9 and 0.1
    burner_island_split = _island_split(ni_value=90.0, si_value=10.0)

    # Expected NI LPG = total LPG - SI total (assume SI demand is all LPG) = 40 - 10 = 30
    # NI LPG share = 30 / NI total (90) = 1/3
    out = rd.get_ni_lpg_share(burner_fuel_split, burner_island_split)

    assert np.isclose(out, 1 / 3, atol=1e-12)


def test_get_ni_lpg_share_warns_when_ng_share_exceeds_ni_share(caplog):
    # NG share 0.6, NI share 0.5 → should log a warning
    burner_fuel_split = _fuel_split(ng_value=60.0, lpg_value=40.0)
    burner_island_split = _island_split(ni_value=50.0, si_value=50.0)

    with caplog.at_level("WARNING"):
        _ = rd.get_ni_lpg_share(burner_fuel_split, burner_island_split)

    assert any(
        "Natural gas share exceeds NI burner share" in r.message for r in caplog.records
    )


def test_get_ni_lpg_share_warns_on_supply_balance_mismatch(caplog):
    # Fuel split: NG=60, LPG=40
    burner_fuel_split = _fuel_split(ng_value=60.0, lpg_value=40.0)
    # Island totals: NI=50, SI=35 → NI LPG = 40-35 = 5; NG + NI LPG = 65 ≠ NI total (50) → warn
    burner_island_split = _island_split(ni_value=50.0, si_value=35.0)

    with caplog.at_level("WARNING"):
        _ = rd.get_ni_lpg_share(burner_fuel_split, burner_island_split)

    assert any(
        "Mismatch between NI demand and (NGA + LPG) supply" in r.message
        for r in caplog.records
    )


def test_get_ni_lpg_share_raises_on_zero_ni_total():
    # Division-by-zero edge case: NI total is 0 (should raise ZeroDivisionError)
    burner_fuel_split = _fuel_split(ng_value=10.0, lpg_value=90.0)
    burner_island_split = _island_split(ni_value=0.0, si_value=100.0)

    with pytest.raises(ZeroDivisionError):
        _ = rd.get_ni_lpg_share(burner_fuel_split, burner_island_split)
