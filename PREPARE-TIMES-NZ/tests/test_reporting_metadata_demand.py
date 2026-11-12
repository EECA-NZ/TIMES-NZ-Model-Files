"""Tests for demand-device reporting metadata builders."""

import pandas as pd
import pytest
from prepare_times_nz.reporting_metadata.demand import (
    DEMAND_COLUMNS,
    build_agriculture_processes,
    build_commercial_processes,
    build_demand_commodities,
    build_industry_processes,
    build_residential_processes,
    build_transport_processes,
    combine_demand_processes,
)


def _demand_row(process: str, commodity: str) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Process": [process],
            "CommodityOut": [commodity],
            "Sector": ["Example sector"],
            "EnduseGroup": ["Example group"],
            "EndUse": ["Example end use"],
            "TechnologyGroup": ["Example technology group"],
            "Technology": ["Example technology"],
        }
    )


def _overrides() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "Process",
            "CommodityOut",
            "SectorGroup",
            "Sector",
            "EnduseGroup",
            "EndUse",
            "TechnologyGroup",
            "Technology",
        ]
    )


def _transport_technology_labels() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Pattern": ["ICEPET"],
            "Technology": ["Internal Combustion Engine (Petrol)"],
            "TechnologyGroup": ["Internal Combustion Engine"],
        }
    )


def _build_demand_processes(
    industry_base,
    industry_future,
    residential,
    commercial_base,
    commercial_future,
    agriculture_base,
    agriculture_future,
    transport_base,
    transport_future,
    transport_commodity_labels,
    transport_technology_labels,
    industry_overrides,
    commercial_overrides,
):
    return combine_demand_processes(
        [
            build_industry_processes(
                industry_base, industry_future, industry_overrides
            ),
            build_residential_processes(residential),
            build_commercial_processes(
                commercial_base, commercial_future, commercial_overrides
            ),
            build_agriculture_processes(agriculture_base, agriculture_future),
            build_transport_processes(
                transport_base,
                transport_future,
                transport_commodity_labels,
                transport_technology_labels,
            ),
        ]
    )


def test_build_demand_processes_labels_transport_and_residential_rows():
    residential = _demand_row("RES-DD-ELC", "DD-LIGHT")
    residential["DwellingType"] = "Detached"
    transport_base = pd.DataFrame(
        {"TechName": ["T_P_CICEPET_LOW"], "Comm-Out": ["T_P_Car"]}
    )
    transport_commodities = pd.DataFrame(
        {
            "CommodityOut": ["T_P_Car"],
            "Sector": ["Road Transport"],
            "EnduseGroup": ["Light vehicles"],
            "EndUse": ["Light Passenger Vehicle"],
        }
    )

    result = _build_demand_processes(
        _demand_row("IND-ELC", "IND-DEM"),
        _demand_row("IND-FUT", "IND-FUT-DEM"),
        residential,
        _demand_row("COM-ELC", "COM-DEM"),
        _demand_row("COM-FUT", "COM-FUT-DEM"),
        _demand_row("AGR-ELC", "AGR-DEM"),
        _demand_row("AGR-FUT", "AGR-FUT-DEM"),
        transport_base,
        transport_base,
        transport_commodities,
        _transport_technology_labels(),
        _overrides(),
        _overrides(),
    )

    assert result.columns.tolist() == DEMAND_COLUMNS
    residential_row = result.loc[result["Process"] == "RES-DD-ELC"].iloc[0]
    assert residential_row["Sector"] == "Detached Dwelling"
    transport_row = result.loc[result["Process"] == "T_P_CICEPET_LOW"].iloc[0]
    assert transport_row["Technology"] == "Internal Combustion Engine (Petrol)"
    assert transport_row["Utilisation"] == "Low"
    assert transport_row["ClassificationMethod"] == "RuleGenerated"


def test_build_demand_processes_applies_complete_overrides():
    override = pd.DataFrame(
        {
            "Process": ["IND-ELC"],
            "CommodityOut": ["OVERRIDE-DEM"],
            "SectorGroup": ["Industry"],
            "Sector": ["Overridden sector"],
            "EnduseGroup": ["Overridden group"],
            "EndUse": ["Overridden end use"],
            "TechnologyGroup": ["Overridden technology group"],
            "Technology": ["Overridden technology"],
        }
    )
    transport = pd.DataFrame({"TechName": ["T_P_CICEPET_LOW"], "Comm-Out": ["T_P_Car"]})
    transport_commodities = pd.DataFrame(
        {
            "CommodityOut": ["T_P_Car"],
            "Sector": ["Road Transport"],
            "EnduseGroup": ["Light vehicles"],
            "EndUse": ["Light Passenger Vehicle"],
        }
    )

    result = _build_demand_processes(
        _demand_row("IND-ELC", "IND-DEM"),
        _demand_row("IND-FUT", "IND-FUT-DEM"),
        _demand_row("RES-ELC", "RES-DEM").assign(DwellingType="Joined"),
        _demand_row("COM-ELC", "COM-DEM"),
        _demand_row("COM-FUT", "COM-FUT-DEM"),
        _demand_row("AGR-ELC", "AGR-DEM"),
        _demand_row("AGR-FUT", "AGR-FUT-DEM"),
        transport,
        transport,
        transport_commodities,
        _transport_technology_labels(),
        override,
        _overrides(),
    )

    row = result.loc[result["Process"] == "IND-ELC"].iloc[0]
    assert row["CommodityOut"] == "OVERRIDE-DEM"
    assert row["ClassificationMethod"] == "Exception"
    assert build_demand_commodities(result)["Commodity"].tolist()[0] == "AGR-DEM"


def test_build_demand_processes_rejects_unlabelled_transport_process():
    transport = pd.DataFrame({"TechName": ["T_P_UNKNOWN_LOW"], "Comm-Out": ["T_P_Car"]})
    transport_commodities = pd.DataFrame(
        {
            "CommodityOut": ["T_P_Car"],
            "Sector": ["Road Transport"],
            "EnduseGroup": ["Light vehicles"],
            "EndUse": ["Light Passenger Vehicle"],
        }
    )

    with pytest.raises(ValueError, match="no technology label"):
        _build_demand_processes(
            _demand_row("IND-ELC", "IND-DEM"),
            _demand_row("IND-FUT", "IND-FUT-DEM"),
            _demand_row("RES-ELC", "RES-DEM").assign(DwellingType="Joined"),
            _demand_row("COM-ELC", "COM-DEM"),
            _demand_row("COM-FUT", "COM-FUT-DEM"),
            _demand_row("AGR-ELC", "AGR-DEM"),
            _demand_row("AGR-FUT", "AGR-FUT-DEM"),
            transport,
            transport,
            transport_commodities,
            _transport_technology_labels(),
            _overrides(),
            _overrides(),
        )
