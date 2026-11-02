"""Tests for the shared commercial service-commodity naming rule."""

import pandas as pd
import pytest
from prepare_times_nz.stage_2.commercial.common import (
    create_service_commodity,
    create_service_commodity_from_tech_names,
)


def test_newtech_service_commodities_match_the_baseyear_rule():
    """New technologies must supply the same service commodities as base year."""
    tech_names = pd.Series(
        ["C_EDU-SH-Boiler-PLT", "C_HLTH-PH-Boiler-H2R", "C_WSR-WH-AirHP-ELC"]
    )

    result = create_service_commodity_from_tech_names(tech_names)
    expected = create_service_commodity(
        pd.Series(["C_EDU", "C_HLTH", "C_WSR"]),
        pd.Series(["SH", "PH", "WH"]),
    )

    assert (
        result.tolist()
        == expected.tolist()
        == [
            "C_EDU-SH",
            "C_HLTH-PH",
            "C_WSR-WH",
        ]
    )


def test_newtech_service_commodity_rejects_malformed_technology_name():
    """Technology names must contain a sector and end-use code."""
    with pytest.raises(ValueError, match="sector-end-use"):
        create_service_commodity_from_tech_names(pd.Series(["C_EDU"]))
