"""Small calculation checks for the disposable report demo."""

import pandas as pd
import pytest

from qa_times_nz.demo_report import (
    biomass_demand,
    changed_periods,
    chart_figure,
    comparison_accordion,
    detail_chart,
    different_period_spans,
    electricity_demand,
    electricity_generation,
    emissions_by_sector,
    fill_report_zeroes,
    fuel_demand,
    natural_gas_demand,
    natural_gas_supply,
    nz_timestamp,
    objective_value,
    period_comparison,
    road_fuel_demand,
)


def test_comparison_tables_preserve_groups_and_handle_zero_baselines():
    baseline = pd.DataFrame(
        {
            "Type": ["B", "A", "A"],
            "Period": [2030, 2040, 2030],
            "Value": [100, 0, 0],
            "Input": ["Baseline: <old>"] * 3,
        }
    )
    candidate = baseline.assign(Value=[105, 1, 0], Input="Candidate: new")
    compared = period_comparison([baseline, candidate], "Type", 0.05)
    assert list(zip(compared["Type"], compared["Period"])) == [
        ("A", 2030),
        ("A", 2040),
        ("B", 2030),
    ]
    assert compared["Difference"].tolist() == [0, 1, 5]
    assert compared["ExceedsTolerance"].tolist() == [False, True, False]
    assert compared["PercentDifference"].isna().tolist() == [True, True, False]
    content = comparison_accordion([baseline, candidate], "Type", "PJ", 0.05)
    assert content.count('class="over-tolerance"') == 1
    assert "Baseline: &lt;old&gt;" in content
    assert "<details>" in content and "<td>—</td>" in content


def test_total_comparison_does_not_require_a_group_column():
    baseline = pd.DataFrame({"Period": [2030], "Value": [10], "Input": ["Baseline"]})
    candidate = baseline.assign(Value=12, Input="Candidate")
    compared = period_comparison([baseline, candidate], None, 0.05)
    assert compared["Difference"].tolist() == [2]
    assert compared["PercentDifference"].tolist() == [20]
    assert compared["ExceedsTolerance"].tolist() == [True]


def test_emissions_sum_by_sector_and_convert_kt_to_mt():
    frame = pd.DataFrame(
        {
            "Period": ["2030"] * 3,
            "SectorGroup": ["Industry", "Industry", "Transport"],
            "Value": [1000, 2000, 5000],
            "Unit": ["kt CO2e"] * 3,
        }
    )
    result = emissions_by_sector(frame)
    assert result["SectorGroup"].tolist() == ["Industry", "Transport"]
    assert result["Value"].tolist() == [3, 5]
    with pytest.raises(ValueError, match="kt CO2e"):
        emissions_by_sector(frame.assign(Unit="Mt CO2e"))


def test_biomass_demand_combines_wood_and_residues_but_not_biogas():
    frame = pd.DataFrame(
        {
            "Period": ["2030"] * 5,
            "Variable": ["Energy demand"] * 4 + ["Other"],
            "Fuel": ["Wood", "Wood residuals (onsite)", "Wood", "Biogas", "Wood"],
            "SectorGroup": [
                "Industry",
                "Industry",
                "Residential",
                "Industry",
                "Industry",
            ],
            "Unit": ["PJ"] * 5,
            "Value": [10, 20, 5, 100, 200],
        }
    )
    result = biomass_demand(frame)
    assert result["SectorGroup"].tolist() == ["Industry", "Residential"]
    assert result["Value"].tolist() == [30, 5]


def test_nz_timestamp_handles_summer_and_winter_offsets():
    assert nz_timestamp("2026-11-17T03:51:36Z") == "17 Nov 2026, 04:51 PM NZDT"
    assert nz_timestamp("2026-06-01T23:30:00+00:00") == "02 Jun 2026, 11:30 AM NZST"
    with pytest.raises(ValueError, match="timezone"):
        nz_timestamp("2026-11-17T03:51:36")


def test_static_panels_keep_layout_and_scenario_colours():
    for count in (2, 3, 5, 6):
        frame = pd.DataFrame(
            {
                "Period": [2030] * count,
                "Value": [1] * count,
                "Type": [str(index) for index in range(count)],
            }
        )
        frames = [
            frame.assign(Input="Baseline: old"),
            frame.assign(Input="Candidate: new"),
        ]
        figure = chart_figure(frames, "Type", "PJ", 0.05)
        assert len(figure.axes) == count
        for axis in figure.axes:
            assert axis.get_subplotspec().get_gridspec().ncols == min(3, count)
            assert [line.get_color() for line in axis.lines] == ["#447474", "#C346CE"]
            assert axis.get_ylim()[0] == 0
            assert axis.get_legend() is None
    assert "data:image/svg+xml;base64," in detail_chart(frames, "Type", "PJ", 0.05)


def test_report_zeroes_complete_model_years_and_categories_before_comparison():
    scenarios = []
    for label, category, year, value in [
        ("Baseline: old", "A", 2030, 10),
        ("Candidate: new", "B", 2040, 20),
    ]:
        frame = pd.DataFrame({"Input": [label], "Period": [year], "Value": [value]})
        scenarios.append(
            {
                "demand": frame,
                "sector_demand": frame.assign(SectorGroup=category),
                "generation": frame.assign(TechnologyGroup=category),
                "gas_demand": frame.assign(SectorGroup=category),
                "gas_supply": frame.assign(**{"Supply source": category}),
                "diesel_demand": frame.assign(SectorGroup=category),
                "road_diesel": frame.assign(**{"Vehicle class": category}),
                "petrol_demand": frame.assign(SectorGroup=category),
                "road_petrol": frame.assign(**{"Vehicle class": category}),
                "biomass_demand": frame.assign(SectorGroup=category),
                "emissions": frame.assign(SectorGroup=category),
            }
        )
    fill_report_zeroes(scenarios)
    assert scenarios[0]["demand"]["Value"].tolist() == [10, 0]
    assert scenarios[1]["demand"]["Value"].tolist() == [0, 20]
    for key in [
        "sector_demand",
        "generation",
        "gas_demand",
        "gas_supply",
        "diesel_demand",
        "road_diesel",
        "petrol_demand",
        "road_petrol",
        "biomass_demand",
        "emissions",
    ]:
        assert all(len(scenario[key]) == 4 for scenario in scenarios)
        assert scenarios[0][key]["Value"].sum() == 10
        assert scenarios[1][key]["Value"].sum() == 20
        assert set(scenarios[0][key]["Period"]) == {2030, 2040}
    assert (
        changed_periods(scenarios[0]["gas_supply"], scenarios[1]["gas_supply"], 0.05)
        == 2
    )
    missing_in_both = scenarios[1]["gas_demand"].query(
        "Period == 2030 and SectorGroup == 'B'"
    )
    assert missing_in_both["Value"].tolist() == [0]


@pytest.mark.parametrize("fuel", ["Diesel", "Petrol"])
def test_fuel_demand_filters_fuel_and_aggregates_sectors_in_pj(fuel):
    frame = pd.DataFrame(
        {
            "Period": ["2030"] * 5,
            "Fuel": [fuel, fuel, fuel, "Biodiesel", fuel],
            "Variable": ["Energy demand"] * 4 + ["Other"],
            "SectorGroup": [
                "Transport",
                "Transport",
                "Industry",
                "Transport",
                "Transport",
            ],
            "Unit": ["PJ"] * 5,
            "Value": [10, 20, 5, 100, 200],
        }
    )
    result = fuel_demand(frame, fuel)
    assert result["SectorGroup"].tolist() == ["Industry", "Transport"]
    assert result["Value"].tolist() == [5, 30]


def test_natural_gas_summaries_keep_pj_and_separate_supply_sources():
    frame = pd.DataFrame(
        {
            "Period": ["2030"] * 4,
            "Variable": [
                "Energy demand",
                "Energy demand",
                "Primary Energy Production",
                "Primary Energy Production",
            ],
            "Fuel": ["Natural gas", "Electricity", "Natural gas", "LNG"],
            "SectorGroup": ["Industry", "Industry", None, None],
            "Unit": ["PJ"] * 4,
            "Value": [36, 72, 100, 20],
        }
    )
    demand = natural_gas_demand(frame)
    supply = natural_gas_supply(frame)
    assert demand["Value"].tolist() == [36]
    assert demand["SectorGroup"].tolist() == ["Industry"]
    assert supply["Supply source"].tolist() == ["Domestic natural gas", "LNG imports"]
    assert supply["Value"].tolist() == [100, 20]


@pytest.mark.parametrize("fuel", ["Diesel", "Petrol"])
def test_road_fuel_groups_vehicle_classes_and_excludes_rail_and_other_fuels(fuel):
    frame = pd.DataFrame(
        {
            "Period": ["2030"] * 6,
            "Fuel": [fuel] * 4 + ["Biodiesel", fuel],
            "Variable": ["Energy demand"] * 5 + ["Other"],
            "SectorGroup": ["Transport"] * 6,
            "Sector": ["Road Transport"] * 3
            + ["Rail Transport", "Road Transport", "Road Transport"],
            "EndUse": [
                "Heavy Truck",
                "Heavy Truck",
                "Bus",
                "Freight Rail",
                "Bus",
                "Bus",
            ],
            "Unit": ["PJ"] * 6,
            "Value": [10, 20, 5, 100, 200, 300],
        }
    )
    result = road_fuel_demand(frame, fuel)
    assert result["Vehicle class"].tolist() == ["Bus", "Heavy Truck"]
    assert result["Value"].tolist() == [5, 30]


def test_changed_periods_compares_totals_with_chart_tolerance():
    baseline = pd.DataFrame(
        {"Period": [2030, 2030, 2040, 2050], "Value": [40, 60, 0, 10]}
    )
    candidate = pd.DataFrame({"Period": [2030, 2040, 2050], "Value": [105, 0, 11]})
    assert changed_periods(baseline, candidate, 0.05) == 1
    assert changed_periods(baseline, candidate, 0) == 2
    assert changed_periods(baseline, candidate.iloc[:2], 0.05) == 1


def test_electricity_demand_filters_aggregates_and_converts():
    frame = pd.DataFrame(
        {
            "Variable": ["Energy demand"] * 4,
            "Fuel": ["Electricity", "Electricity", "Gas", "Electricity"],
            "SectorGroup": ["Industry", "Commercial", "Industry", "Industry"],
            "Period": ["2030", "2030", "2030", "2040"],
            "Unit": ["PJ"] * 4,
            "Value": [3.6, 7.2, 100, 18],
        }
    )
    result = electricity_demand(frame)
    assert result["Period"].tolist() == [2030, 2040]
    assert result["Value"].tolist() == pytest.approx([3, 5])
    sectors = electricity_demand(frame, ["SectorGroup"])
    assert sectors["SectorGroup"].tolist() == ["Commercial", "Industry", "Industry"]
    assert sectors["Value"].tolist() == pytest.approx([2, 1, 5])
    assert sectors["Value"].sum() == pytest.approx(result["Value"].sum())
    frame.loc[0, "Period"] = "2030.5"
    with pytest.raises(ValueError, match="integer annual"):
        electricity_demand(frame)


def test_tolerance_highlights_only_different_periods():
    baseline = dict(
        zip([2025, 2030, 2035, 2040, 2045, 2050], [100, 100, 100, 0, 0, 10])
    )
    candidate = dict(zip([2025, 2030, 2035, 2040, 2045], [104, 105, 106, 0, 1]))
    assert list(different_period_spans(baseline, candidate, 0.05)) == [
        (2032.5, 2037.5),
        (2042.5, 2047.5),
        (2047.5, 2050),
    ]


def test_objective_requires_one_value_in_expected_units():
    frame = pd.DataFrame({"Value": [123.0], "Unit": ["NZDb"]})
    assert objective_value(frame) == 123
    with pytest.raises(ValueError, match="one objective"):
        objective_value(pd.concat([frame, frame]))
    with pytest.raises(ValueError, match="one objective"):
        objective_value(frame.assign(Unit="Mio NZD"))


def test_generation_preserves_types_and_excludes_other_variables():
    frame = pd.DataFrame(
        {
            "Variable": ["Electricity generation"] * 3 + ["Electricity fuel use"],
            "TechnologyGroup": ["Hydro", "Hydro", "Wind", "Thermal"],
            "Period": ["2030"] * 4,
            "Unit": ["PJ"] * 4,
            "Value": [3.6, 7.2, 18, 100],
        }
    )
    result = electricity_generation(frame)
    assert result["TechnologyGroup"].tolist() == ["Hydro", "Wind"]
    assert result["Value"].tolist() == pytest.approx([3, 5])
