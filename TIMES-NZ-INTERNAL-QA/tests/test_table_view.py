"""Focused tests for explorer table-view data and choices."""

import unittest

import polars as pl
from times_nz_internal_qa.app.helpers.data_processing import (
    make_display_table_data,
    make_table_data,
)
from times_nz_internal_qa.app.helpers.server_functions import _detail_group_columns
from times_nz_internal_qa.app.helpers.ui_elements import chart_type_choices


class _Inputs:  # pylint: disable=too-few-public-methods
    """Minimal callable-input stand-in for filter-grain tests."""

    def __init__(self, values):
        for input_id, value in values.items():
            setattr(self, input_id, lambda value=value: value)


class DetailGroupColumnTests(unittest.TestCase):
    """Verify table grain responds to grouping and active filter selections."""

    def test_includes_selected_group_and_only_active_filters(self):
        """Inactive filters are omitted and duplicate grouping columns collapse."""
        filters = [
            {"chart_id": "chart", "id": "technology", "col": "Technology"},
            {"chart_id": "chart", "id": "region", "col": "Region"},
            {"chart_id": "chart", "id": "fuel", "col": "Fuel"},
        ]
        inputs = _Inputs(
            {
                "filter_chart_technology_selected": ["Wind"],
                "filter_chart_region_selected": ["North Island"],
                "filter_chart_fuel_selected": [],
            }
        )

        result = _detail_group_columns(
            ["Scenario", "Period", "Unit"], "Technology", filters, inputs
        )

        self.assertEqual(
            result,
            ["Scenario", "Period", "Unit", "Technology", "Region"],
        )


class MakeTableDataTests(unittest.TestCase):
    """Verify table rows come directly from filtered model data."""

    def test_uses_only_actual_model_periods(self):
        """Intermediate periods are not completed or interpolated."""
        source = pl.DataFrame(
            {
                "Scenario": ["Base", "Base"],
                "Variable": ["Generation", "Generation"],
                "Period": [2023, 2025],
                "Unit": ["GWh", "GWh"],
                "TechnologyGroup": ["Wind", "Wind"],
                "Value": [10.123456, 14.0],
            }
        )

        download_data = make_table_data(source.lazy())
        result = make_display_table_data(download_data)

        self.assertEqual(
            download_data.collect().get_column("Value").to_list(),
            [10.123456, 14.0],
        )
        self.assertEqual(
            result.columns,
            ["Scenario", "Variable", "Year", "Unit", "TechnologyGroup", "Value"],
        )
        self.assertEqual(result.get_column("Year").to_list(), [2023, 2025])
        self.assertNotIn(2024, result.get_column("Year").to_list())
        self.assertEqual(
            result.get_column("TechnologyGroup").to_list(), ["Wind", "Wind"]
        )
        self.assertEqual(result.get_column("Value").to_list(), [10.1235, 14.0])

    def test_includes_timeslice_and_sorts_rows(self):
        """Timeslice identifiers remain visible and rows have stable ordering."""
        source = pl.DataFrame(
            {
                "Scenario": ["Second", "Base", "Base"],
                "Variable": ["Generation"] * 3,
                "Period": [2030, 2030, 2025],
                "TimeSlice": ["WIN-WK-D", "SUM-WE-P", "SPR-WK-N"],
                "Unit": ["GW"] * 3,
                "Technology": ["Wind", "Solar", "Wind"],
                "Value": [3.0, 2.0, 1.0],
            }
        )

        download_data = make_table_data(source)
        collected_download = download_data.collect()
        result = make_display_table_data(download_data)

        self.assertEqual(
            collected_download.get_column("TimeSlice").to_list(),
            ["WIN-WK-D", "SUM-WE-P", "SPR-WK-N"],
        )
        self.assertEqual(
            collected_download.get_column("TimeSliceLabel").to_list(),
            [
                "Winter / Weekday / Day",
                "Summer / Weekend / Peak",
                "Spring / Weekday / Night",
            ],
        )
        self.assertEqual(
            result.columns,
            [
                "Scenario",
                "Variable",
                "Year",
                "Unit",
                "Technology",
                "Value",
                "TimeSlice",
            ],
        )
        self.assertEqual(
            result.get_column("Scenario").to_list(), ["Base", "Base", "Second"]
        )
        self.assertEqual(result.get_column("Year").to_list(), [2025, 2030, 2030])
        self.assertEqual(
            result.get_column("TimeSlice").to_list(),
            [
                "Spring / Weekday / Night",
                "Summer / Weekend / Peak",
                "Winter / Weekday / Day",
            ],
        )
        self.assertEqual(
            result.get_column("Technology").to_list(), ["Wind", "Solar", "Wind"]
        )
        self.assertEqual(result.get_column("Value").to_list(), [1.0, 2.0, 3.0])

    def test_retains_all_detail_columns(self):
        """Dimensions unrelated to the selected chart grouping remain visible."""
        source = pl.DataFrame(
            {
                "Scenario": ["Base"],
                "Variable": ["Generation"],
                "Period": [2030],
                "Unit": ["GWh"],
                "TechnologyGroup": ["Renewables"],
                "Technology": ["Onshore wind"],
                "Region": ["North Island"],
                "Value": [20.0],
            }
        )

        result = make_display_table_data(make_table_data(source))

        self.assertEqual(result.get_column("TechnologyGroup").to_list(), ["Renewables"])
        self.assertEqual(result.get_column("Technology").to_list(), ["Onshore wind"])
        self.assertEqual(result.get_column("Region").to_list(), ["North Island"])


class ChartTypeChoiceTests(unittest.TestCase):
    """Verify view choices for standard and timeslice sections."""

    def test_standard_sections_have_four_views(self):
        """Standard sections offer all three charts plus a table."""
        self.assertEqual(list(chart_type_choices()), ["bar", "line", "area", "table"])

    def test_timeslice_sections_have_bar_and_table_views(self):
        """Timeslice sections retain Bar and also offer Table."""
        self.assertEqual(list(chart_type_choices("timeslice")), ["bar", "table"])


if __name__ == "__main__":
    unittest.main()
