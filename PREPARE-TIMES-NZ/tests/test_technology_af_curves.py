"""Tests for technology AF curve helpers."""

import sys
import types

fake_stage_0_settings = types.ModuleType("prepare_times_nz.stage_0.stage_0_settings")
fake_stage_0_settings.BASE_YEAR = 2023
sys.modules.setdefault(
    "prepare_times_nz.stage_0.stage_0_settings", fake_stage_0_settings
)

# pylint: disable=wrong-import-position
from prepare_times_nz.stage_4.technology_af_curves import wildcard_technology_codes


def test_wildcard_technology_codes_collapses_differing_token():
    """Residential wildcarding should replace the technology token."""
    result = wildcard_technology_codes(
        "Residential",
        ["RES-JD-ELC-HPSH-S_HEAT", "RES-JD-ELC-HEATR-S_HEAT"],
    )

    assert result == "RES-JD-ELC-*-S_HEAT"


def test_wildcard_technology_codes_keeps_exact_match():
    """Single residential codes should still wildcard the technology token."""
    result = wildcard_technology_codes("Residential", ["RES-JD-ELC-HWATER_C-WH_LOW"])

    assert result == "RES-JD-ELC-*-WH_LOW"


def test_wildcard_technology_codes_uses_commercial_technology_slot():
    """Commercial wildcarding should use the commercial technology slot."""
    result = wildcard_technology_codes(
        "Commercial",
        ["C_EDU-SH-AIRHP-ELC", "C_EDU-SH-RH-ELC"],
    )

    assert result == "C_EDU-SH-*-ELC"
