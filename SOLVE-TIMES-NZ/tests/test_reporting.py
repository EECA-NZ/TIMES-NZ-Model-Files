"""Summary calculations use synthetic frames, never local result archives."""

import pandas as pd
import pytest

from solve_times_nz.reporting import (
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
    assert result["renewable_generation_share"].Value.item() == pytest.approx(0.25)
    assert result["renewable_tfec_share"].Value.item() == pytest.approx(0.375)
    assert result["renewable_tfec_share"].Unit.item() == "Share"


def test_renewable_matching_keeps_region_and_vintage_and_rejects_missing_inputs():
    other = generation().assign(Region="SI", Vintage=2025)
    other.loc[other.Fuel.eq("Biogas"), "Value"] = 40
    other.loc[other.Fuel.eq("Coal"), "Value"] = 0
    combined = pd.concat([generation(), other])
    result = renewable_shares(combined, demand(), fuels())
    assert result["renewable_generation_share"].Value.item() == pytest.approx(0.625)
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
    assert result["renewable_generation_share"].Value.isna().all()
    assert result["renewable_tfec_share"].Value.isna().all()
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
        "transport_capacity.parquet": use.iloc[:1].assign(
            Variable="Transport Capacity",
            TechnologyGroup="Battery Electric Vehicle",
            EndUse="Light Passenger Vehicle",
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
    assert result["qa_demand.csv"].Value.item() == pytest.approx(20 / 3.6)
    assert result["qa_generation_total.csv"].Value.item() == pytest.approx(20 / 3.6)
    assert result["qa_emissions_total.csv"].Value.item() == 1
    assert result["qa_objective.csv"].Value.item() == 1.5
    assert result["transport_lpv_capacity.csv"].TechnologyGroup.item() == "BEV"
    assert result["indicator_ren_gen.csv"].Value.item() == 25
    assert result["renewable_generation_share.csv"].Value.item() == 0.25
    assert "total_demand_by_fuel.csv" in result
    assert all(
        frame.Period.dtype == "int64" for frame in result.values() if "Period" in frame
    )


def test_legacy_industrial_publication_exclusions_do_not_change_full_qa_totals():
    frame = pd.concat([demand().iloc[[0]]] * 4, ignore_index=True).assign(
        SectorGroup="Industry",
        Sector="Other industry",
        EndUse="Low Temperature Heat (<100 C), Process Requirements",
        Fuel=["Coal", "Fuel oil", "Wood residuals (onsite)", "Wood"],
        Value=[2.0, 3.0, 4.0, 5.0],
    )
    result = demand_summaries(frame, frame)
    assert result["industrial_demand"].Value.sum() == 7
    assert result["demand_profile_industrial_process_heat"].Value.sum() == 7
    assert result["total_demand_by_fuel"].Value.sum() == 14
    assert result["qa_biomass_demand"].Value.sum() == 9


def test_publication_small_value_cleanup_does_not_round_qa_gas_supply():
    frame = demand().iloc[[0]].assign(Fuel="Natural gas", Value=1e-8)
    result = supply_summaries(frame)
    assert result["primary_energy_lng_natural_gas_supply"].Value.item() == 0
    assert result["qa_gas_supply"].Value.item() == 1e-8
