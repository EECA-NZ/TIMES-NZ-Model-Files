"""Unit tests for the base/SubRES biofuel split."""

import pandas as pd
from prepare_times_nz.stage_4.biofuels import (
    FUTURE_BIOFUEL_CONVERSIONS,
    split_biofuel_parameters,
    split_future_biofuel_processes,
)


def test_future_biofuel_processes_are_declared_only_in_subres() -> None:
    """Future conversion processes retain their units but leave the base workbook."""
    base, future = split_future_biofuel_processes()

    assert set(future["TechName"]) == FUTURE_BIOFUEL_CONVERSIONS
    assert not set(base["TechName"]).intersection(FUTURE_BIOFUEL_CONVERSIONS)
    assert future.set_index("TechName").loc["WSTWOD2WOD", "Tcap"] == "PJa"
    assert future.set_index("TechName").loc["CT_CWODBPL", "Tcap"] == "GWth"


def test_future_biofuel_parameter_continuations_stay_with_their_process(
    tmp_path,
) -> None:
    """Blank-name topology continuation rows follow their preceding process."""
    plant_processes_path = tmp_path / "plant_processes.csv"
    pd.DataFrame(
        {
            "TechName": ["LEGACY", "WSTWOD2WOD", "", "", ""],
            "Comm-IN": ["COA", "WODWST", "", "ELC", ""],
            "Comm-OUT": ["ELC", "WOD", "OSWOD", "WOD", "OSWOD"],
        }
    ).to_csv(plant_processes_path, index=False)

    base, future = split_biofuel_parameters(plant_processes_path)

    assert base["TechName"].tolist() == ["LEGACY"]
    owners = future["TechName"].ffill()
    assert set(owners) == {"WSTWOD2WOD"}

    wood_waste = future.loc[owners.eq("WSTWOD2WOD")]
    assert (
        wood_waste[["Comm-IN", "Comm-OUT"]].dropna(how="all").fillna("").values.tolist()
    ) == [
        ["WODWST", "WOD"],
        ["", "OSWOD"],
        ["ELC", "WOD"],
        ["", "OSWOD"],
    ]
