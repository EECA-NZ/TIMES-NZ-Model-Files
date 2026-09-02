"""Focused tests for explorer table-view data and choices."""

import unittest

import polars as pl
from times_nz_internal_qa.app.helpers.data_processing import make_table_data
from times_nz_internal_qa.app.helpers.ui_elements import chart_type_choices


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

        result = make_table_data(source.lazy(), "TechnologyGroup")

        self.assertEqual(
            result.columns,
            ["Scenario", "Year", "Unit", "Wind"],
        )
        self.assertEqual(result.get_column("Year").to_list(), [2023, 2025])
        self.assertNotIn(2024, result.get_column("Year").to_list())
        self.assertEqual(result.get_column("Wind").to_list(), [10.1235, 14.0])

    def test_includes_timeslice_and_sorts_rows(self):
        """Timeslice identifiers remain visible and rows have stable ordering."""
        source = pl.DataFrame(
            {
                "Scenario": ["Second", "Base", "Base"],
                "Variable": ["Generation"] * 3,
                "Period": [2030, 2030, 2025],
                "TimeSlice": ["S2", "S1", "S2"],
                "Unit": ["GW"] * 3,
                "Technology": ["Wind", "Solar", "Wind"],
                "Value": [3.0, 2.0, 1.0],
            }
        )

        result = make_table_data(source, "Technology")

        self.assertEqual(
            result.columns,
            ["Scenario", "Year", "TimeSlice", "Unit", "Solar", "Wind"],
        )
        self.assertEqual(
            result.get_column("Scenario").to_list(), ["Base", "Base", "Second"]
        )
        self.assertEqual(result.get_column("Year").to_list(), [2025, 2030, 2030])
        self.assertEqual(result.get_column("Solar").to_list(), [None, 2.0, None])
        self.assertEqual(result.get_column("Wind").to_list(), [1.0, None, 3.0])

    def test_total_group_is_retained(self):
        """The synthetic Total grouping remains visible in the table."""
        source = pl.DataFrame(
            {
                "Scenario": ["Base"],
                "Variable": ["Generation"],
                "Period": [2030],
                "Unit": ["GWh"],
                "Grouping": ["Total"],
                "Value": [20.0],
            }
        )

        result = make_table_data(source, "Grouping")

        self.assertEqual(result.columns, ["Scenario", "Year", "Unit", "Total"])
        self.assertEqual(result.get_column("Total").to_list(), [20.0])


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
