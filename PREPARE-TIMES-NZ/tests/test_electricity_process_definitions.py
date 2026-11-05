"""Tests for electricity process declarations used by the TIMES builder."""

import pandas as pd
from prepare_times_nz.stage_4.electricity.new_storage import (
    create_battery_process_file,
)


def test_battery_processes_use_elc_as_primary_commodity_group() -> None:
    batteries = pd.DataFrame({"TechName": ["ELC_BAT_2H", "ELC_BAT_DIST"]})

    result = create_battery_process_file(batteries)

    assert result["Sets"].tolist() == ["ELE, STG", "ELE, STG"]
    assert result["PrimaryCG"].tolist() == ["ELC", "ELC"]
