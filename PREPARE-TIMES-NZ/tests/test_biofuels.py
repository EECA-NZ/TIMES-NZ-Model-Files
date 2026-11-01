"""Regression tests for the base/SubRES biofuel split."""

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


def test_future_biofuel_parameter_continuations_stay_with_their_process() -> None:
    """Blank-name topology continuation rows follow their preceding process."""
    base, future = split_biofuel_parameters()

    assert not set(base["TechName"].dropna()).intersection(FUTURE_BIOFUEL_CONVERSIONS)
    owners = future["TechName"].ffill()
    assert set(owners) == FUTURE_BIOFUEL_CONVERSIONS

    wood_waste = future.loc[owners.eq("WSTWOD2WOD")]
    assert (
        wood_waste[["Comm-IN", "Comm-OUT"]].dropna(how="all").fillna("").values.tolist()
    ) == [
        ["WODWST", "WOD"],
        ["", "OSWOD"],
        ["ELC", "WOD"],
        ["", "OSWOD"],
    ]
