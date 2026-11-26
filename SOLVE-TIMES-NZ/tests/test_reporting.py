"""Summary calculations use synthetic frames, never local result archives."""

from pathlib import Path

import pandas as pd
import pytest

from solve_times_nz.reporting import (
    _peak_demand,
    aggregate,
    build_summaries,
    complete,
    demand_summaries,
    renewable_shares,
    supply_summaries,
)
from solve_times_nz.reporting_flows import (
    TIMESLICES,
    equivalent_flex_input,
    flow_summaries,
    timeslice_view,
)


def generation():
    return pd.DataFrame(
        {
            "Scenario": ["s"] * 3,
            "Period": [2030] * 3,
            "Region": ["NI"] * 3,
            "Process": ["plant"] * 3,
            "Vintage": [2020] * 3,
            "Unit": ["PJ"] * 3,
            "Variable": [
                "Electricity fuel use",
                "Electricity fuel use",
                "Electricity generation",
            ],
            "Fuel": ["Biogas", "Coal", "Electricity"],
            "Value": [10.0, 30.0, 20.0],
            "TechnologyGroup": ["Thermal"] * 3,
        }
    )


def fuels():
    return pd.DataFrame(
        {
            "Fuel": ["Biogas", "Coal", "Electricity", "Wood"],
            "Renewable": ["Renewable", "Non-renewable", "Electricity", "Renewable"],
        }
    )


def demand():
    return pd.DataFrame(
        {
            "Scenario": ["s"] * 5,
            "Period": [2030] * 5,
            "Unit": ["PJ"] * 5,
            "Variable": ["Energy demand"] * 5,
            "Region": ["NI"] * 5,
            "SectorGroup": ["Residential"] * 5,
            "Sector": ["Residential"] * 5,
            "EndUse": [
                "Heat",
                "Heat",
                "Heat",
                "International Aviation",
                "International Shipping",
            ],
            "Fuel": ["Electricity", "Coal", "Wood", "Coal", "Coal"],
            "Value": [20.0, 10.0, 10.0, 100.0, 100.0],
        }
    )


def test_completion_fills_absent_rows_but_preserves_existing_null_values():
    frame = pd.DataFrame(
        {
            "Scenario": ["s", "s"],
            "Period": [2030, 2040],
            "Unit": ["PJ"] * 2,
            "Fuel": ["Coal", "Wood"],
            "Value": [float("nan"), 2.0],
        }
    )
    result = complete(
        frame, pd.DataFrame({"Scenario": ["s", "s"], "Period": [2030, 2040]})
    )
    assert len(result) == 4
    assert result.Value.isna().sum() == 1
    assert result.Value.eq(0).sum() == 2
    assert result.Value.sum() == 2
    with pytest.raises(ValueError, match="Duplicate summary"):
        complete(pd.concat([frame, frame]), frame[["Scenario", "Period"]])


def test_aggregation_normalizes_legacy_years_and_rejects_lost_classifications():
    frame = demand().assign(Period="2030")
    result = aggregate(frame, ["Fuel"])
    assert result.Period.dtype == "int64"
    assert result.Value.sum() == 240
    frame.loc[0, "Fuel"] = None
    with pytest.raises(ValueError, match="Missing summary"):
        aggregate(frame, ["Fuel"])


def test_renewable_shares_allocate_mixed_fuels_and_exclude_international_transport():
    result = renewable_shares(generation(), demand(), fuels())
    assert result[
        "indicators/renewable_generation_share"
    ].Value.item() == pytest.approx(0.25)
    assert result["indicators/renewable_tfec_share"].Value.item() == pytest.approx(
        0.375
    )
    assert result["indicators/renewable_tfec_share"].Unit.item() == "Share"


def test_renewable_matching_keeps_region_and_vintage_and_rejects_missing_inputs():
    other = generation().assign(Region="SI", Vintage=2025)
    other.loc[other.Fuel.eq("Biogas"), "Value"] = 40
    other.loc[other.Fuel.eq("Coal"), "Value"] = 0
    combined = pd.concat([generation(), other])
    result = renewable_shares(combined, demand(), fuels())
    assert result[
        "indicators/renewable_generation_share"
    ].Value.item() == pytest.approx(0.625)
    with pytest.raises(ValueError, match="Missing renewable fuel classification"):
        renewable_shares(combined, demand(), fuels().loc[fuels().Fuel.ne("Biogas")])
    broken = generation()
    broken.loc[broken.Variable.eq("Electricity generation"), "Vintage"] = 2030
    with pytest.raises(ValueError, match="Missing fuel-use renewable share"):
        renewable_shares(broken, demand(), fuels())


def test_zero_denominators_remain_undefined_instead_of_becoming_zero():
    result = renewable_shares(
        generation().assign(Value=0), demand().assign(Value=0), fuels()
    )
    assert result["indicators/renewable_generation_share"].Value.isna().all()
    assert result["indicators/renewable_tfec_share"].Value.isna().all()
    with pytest.raises(ValueError, match="Recorded.*Renewable"):
        renewable_shares(generation(), demand(), fuels().drop(columns="Renewable"))


def test_flow_conversion_preserves_sign_and_completes_missing_timeslices():
    frame = pd.DataFrame(
        {
            "Scenario": ["s", "s"],
            "Period": [2035, 2035],
            "Variable": ["Battery charging", "Battery discharging"],
            "Technology": ["Battery"] * 2,
            "TimeSlice": [TIMESLICES[0]] * 2,
            "Value": [1.0, 0.8],
            "Unit": ["PJ"] * 2,
        }
    )
    weights = pd.DataFrame({"TimeSlice": TIMESLICES, "YearFraction": [1 / 24] * 24})
    result = timeslice_view(frame, weights, "GW")
    assert len(result) == 48
    assert result.Value.eq(0).sum() == 46
    charge = result.loc[result.Variable.eq("Battery charging")]
    assert charge.Value.sum() == pytest.approx(-277.77777778 / (8760 / 24))
    assert set(result.TimeSlice) == set(TIMESLICES)
    assert result.TimeSliceOrder.min() == 0 and result.TimeSliceOrder.max() == 23
    with pytest.raises(ValueError, match="recorded timeslice weights"):
        timeslice_view(frame, weights.iloc[1:], "GW")


def test_flex_equivalent_input_matches_process_year_region_and_timeslice():
    raw = pd.DataFrame(
        {
            "Scenario": ["s"] * 2,
            "Process": ["RES-DD-ELC-HPSH-S_HEAT"] * 2,
            "Region": ["NI"] * 2,
            "Period": ["2035"] * 2,
            "TimeSlice": [TIMESLICES[0]] * 2,
            "Attribute": ["VAR_FIn", "VAR_FOut"],
            "PV": [2.0, 6.0],
        }
    )
    frame = pd.DataFrame(
        {
            "Scenario": ["s"],
            "Process": ["DD-S_HEAT-FLEX"],
            "Region": ["NI"],
            "Period": [2035],
            "TimeSlice": [TIMESLICES[0]],
            "Value": [3.0],
        }
    )
    assert equivalent_flex_input(frame, raw).Value.item() == 1.0
    with pytest.raises(ValueError, match="efficiency"):
        equivalent_flex_input(frame.assign(Region="SI"), raw)
    with pytest.raises(ValueError, match="process mapping"):
        equivalent_flex_input(frame.assign(Process="unknown"), raw)


@pytest.mark.parametrize("year", [2030, "2030"])
def test_build_summaries_includes_demo_objective_indicators_and_publication_tables(
    year,
):
    use = demand().iloc[:3]
    tables = {
        "energy_demand.parquet": use,
        "elec_generation.parquet": generation(),
        "emissions.parquet": use.iloc[:1].assign(Unit="kt CO2e", Value=1000),
        "transport_energy_demand.parquet": use.iloc[:1].assign(
            Variable="Transport Energy Demand"
        ),
        "primary_energy.parquet": use.iloc[:1].assign(
            Variable="Primary Energy Production", Fuel="Natural gas"
        ),
        "batteries.parquet": use.iloc[:1].assign(
            Variable="Capacity", Technology="Battery", Unit="GW"
        ),
        "grid_capacity.parquet": use.iloc[:1]
        .assign(Variable="Capacity", Technology="HVDC link", Unit="GW")
        .pipe(lambda df: pd.concat([df, df.assign(Region="SI")], ignore_index=True)),
        "electricity_demand_by_timeslice.parquet": use.iloc[:1].assign(
            Variable="Average output", Unit="GW", TimeSlice="WIN-WK-P"
        ),
        "transport_capacity.parquet": pd.concat(
            [use.iloc[:1]] * 3, ignore_index=True
        ).assign(
            Variable="Transport Capacity",
            TechnologyGroup="Battery Electric Vehicle",
            EndUse=[
                "Light Passenger Vehicle",
                "Light Commercial Vehicle",
                "Heavy Truck",
            ],
            Value=[1.0, 2.0, 3.0],
            Unit="000vehicles",
        ),
        "battery_flows.parquet": pd.DataFrame(),
        "demand_flex_flows.parquet": pd.DataFrame(),
        "objective_function.parquet": pd.DataFrame(
            {
                "Scenario": ["s"],
                "Unit": ["NZDb"],
                "Variable": ["Objective Function"],
                "Value": [1.5],
            }
        ),
    }
    tables = {
        name: frame.assign(Period=year) if "Period" in frame else frame
        for name, frame in tables.items()
    }
    result = build_summaries(tables, fuels(), pd.DataFrame())
    assert result["electricity/electricity_demand.csv"].Value.item() == pytest.approx(
        20 / 3.6
    )
    assert result[
        "electricity/electricity_generation.csv"
    ].Value.item() == pytest.approx(20 / 3.6)
    assert result["emissions/emissions.csv"].Value.item() == 1
    assert result["electricity/grid_capacity.csv"].Value.item() == use.Value.iloc[0]
    assert result["indicators/objective_function.csv"].Value.item() == 1.5
    fleet = result["transport/transport_capacity.csv"]
    assert fleet.TechnologyGroup.unique().tolist() == ["BEV"]
    assert fleet.set_index("EndUse").Value.to_dict() == {
        "Light Passenger Vehicle": 1,
        "Light Commercial Vehicle": 2,
        "Heavy Truck": 3,
    }
    renewable = result["indicators/renewable_generation_share.csv"]
    assert renewable.set_index("Unit").Value.to_dict() == {"Share": 0.25, "%": 25}
    totals = (
        result["demand/energy_demand_by_fuel.csv"].set_index("Fuel").Value.to_dict()
    )
    assert totals == {"Electricity": 20, "Coal": 10, "Wood": 10}
    assert not any(Path(name).name.startswith("qa_") for name in result)
    assert {Path(name).parent.as_posix() for name in result} == {
        "electricity",
        "demand",
        "supply",
        "transport",
        "emissions",
        "indicators",
    }
    assert "elec_gen_line.csv" not in result
    assert "indicator_ren_gen.csv" not in result
    assert "demand/total_demand_by_fuel.csv" in result
    assert all(
        frame.Period.dtype == "int64" for frame in result.values() if "Period" in frame
    )


def test_peak_demand_sums_regions_and_reports_the_highest_slice():
    rows = pd.DataFrame(
        {
            "Scenario": ["s"] * 6,
            "Period": [2030] * 6,
            "Region": ["NI", "SI", "NI", "SI", "NI", "SI"],
            "TimeSlice": ["SUM-WK-D"] * 2 + ["WIN-WK-P"] * 2 + ["WIN-WK-N"] * 2,
            "Value": [1.0, 1.0, 3.0, 2.0, 4.0, 0.5],
            "Variable": "Average output",
            "Unit": "GW",
        }
    )
    peak = _peak_demand(rows)
    assert peak[["TimeSlice", "Value"]].to_dict("records") == [
        {"TimeSlice": "WIN-WK-P", "Value": 5.0}
    ]


def test_legacy_industrial_publication_exclusions_do_not_change_full_qa_totals():
    frame = pd.concat([demand().iloc[[0]]] * 4, ignore_index=True).assign(
        SectorGroup="Industry",
        Sector="Other industry",
        EndUse="Low Temperature Heat (<100 C), Process Requirements",
        Fuel=["Coal", "Fuel oil", "Wood residuals (onsite)", "Wood"],
        Value=[2.0, 3.0, 4.0, 5.0],
    )
    result = demand_summaries(frame, frame)
    assert result["demand/industrial_demand"].Value.sum() == 7
    assert result["demand/demand_profile_industrial_process_heat"].Value.sum() == 7
    assert result["demand/total_demand_by_fuel"].Value.sum() == 14
    assert result["demand/woody_biomass_demand_by_sector_group"].Value.sum() == 9


def test_publication_small_value_cleanup_does_not_round_natural_gas_supply():
    frame = demand().iloc[[0]].assign(Fuel="Natural gas", Value=1e-8)
    result = supply_summaries(frame)
    assert result["supply/primary_energy_lng_natural_gas_supply"].Value.item() == 0
    assert result["supply/natural_gas_supply_by_source"].Value.item() == 1e-8


def test_consolidated_demand_keeps_fuel_vehicle_and_sector_boundaries():
    frame = pd.concat([demand().iloc[[0]]] * 4, ignore_index=True).assign(
        Fuel=["Diesel", "Petrol", "Electricity", "Electricity"],
        SectorGroup=[
            "Transport",
            "Transport",
            "Industry",
            "Agriculture, Forestry, and Fishing",
        ],
        Sector=["Road Transport", "Road Transport", "Dairy", "Agriculture"],
        EndUse=["Heavy Truck", "Light Passenger Vehicle", "Heat", "Heat"],
        Value=[3.0, 7.0, 9.0, 2.0],
    )
    result = demand_summaries(frame, frame)
    detailed = result["demand/energy_demand_by_fuel_and_sector_group"]
    assert detailed.groupby("Fuel").Value.sum().to_dict() == {
        "Diesel": 3,
        "Petrol": 7,
        "Electricity": 11,
    }
    vehicles = result["transport/road_transport_demand_by_fuel_and_vehicle_class"]
    assert vehicles.set_index(["Fuel", "Vehicle class"]).Value.to_dict() == {
        ("Diesel", "Heavy Truck"): 3,
        ("Petrol", "Light Passenger Vehicle"): 7,
    }
    electricity = result["electricity/electricity_demand_by_sector_group"].set_index(
        "SectorGroup"
    )
    assert electricity.loc["Industry", "Value"] == pytest.approx(9 / 3.6)
    assert electricity.loc[
        "Agriculture, Forestry, and Fishing", "Value"
    ] == pytest.approx(2 / 3.6)
    combined = result[
        "electricity/electricity_demand_by_sector_group_combined_industry"
    ]
    assert combined.SectorGroup.tolist() == ["Industry"]
    assert combined.Value.item() == pytest.approx(11 / 3.6)


def test_consolidated_flows_keep_both_years_units_and_timeslice_completion():
    flows = pd.DataFrame(
        {
            "Scenario": ["s", "s"],
            "Period": [2035, 2050],
            "Variable": ["Battery charging"] * 2,
            "Technology": ["Battery"] * 2,
            "TimeSlice": [TIMESLICES[0]] * 2,
            "Value": [1.0, 2.0],
            "Unit": ["PJ"] * 2,
        }
    )
    weights = pd.DataFrame({"TimeSlice": TIMESLICES, "YearFraction": [1 / 24] * 24})
    result = flow_summaries(
        {"battery_flows.parquet": flows, "demand_flex_flows.parquet": pd.DataFrame()},
        weights,
    )
    assert set(result) == {"electricity/battery_flows"}
    combined = result["electricity/battery_flows"]
    for year, value in [(2035, 1), (2050, 2)]:
        for unit in ["GW", "GWh"]:
            selected = combined.loc[combined.Period.eq(year) & combined.Unit.eq(unit)]
            pd.testing.assert_frame_equal(
                selected.reset_index(drop=True),
                timeslice_view(flows.loc[flows.Period.eq(year)], weights, unit),
            )
            assert len(selected) == 24
            expected = -value * 277.77777778
            if unit == "GW":
                expected /= 8760 / 24
            assert selected.Value.sum() == pytest.approx(expected)
