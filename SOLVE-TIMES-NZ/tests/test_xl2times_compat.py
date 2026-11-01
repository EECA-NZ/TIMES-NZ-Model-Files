"""Regression tests for the project-owned xl2times compatibility hooks."""

import pandas as pd
import pytest
from solve_times_nz.xl2times_compat import (
    _convert_to_veda_precision,
    _drop_generated_residuals_after_legacy_horizon,
    _expand_multi_region_user_constraints,
    _export_implied_emission_topology,
    _output_directory_from_args,
    _project_demands_with_zero_continuation,
    _with_optional_descriptions,
)
from xl2times.datatypes import EmbeddedXlTable, Tag


def test_veda_precision_retains_fifteen_significant_digits() -> None:
    """Keep coefficients at the precision found in VEDA DD exports."""
    tables = {
        "UC_CAP": pd.DataFrame({"value": [0.278596898776721, -0.077999194847021, 1.0]})
    }

    result = _convert_to_veda_precision(tables)

    assert result["UC_CAP"]["value"].tolist() == [
        "0.278596898776721",
        "-0.077999194847021",
        "1",
    ]


def test_output_directory_comes_from_xl2times_argument(tmp_path) -> None:
    """Place the xl2times log in the requested DD output directory."""
    output = tmp_path / "build" / "case"

    assert _output_directory_from_args(["--output_dir", str(output)]) == output
    assert _output_directory_from_args([f"--output_dir={output}"]) == output


def test_optional_description_columns_are_added(monkeypatch) -> None:
    model = type(
        "Model",
        (),
        {
            "processes": pd.DataFrame({"process": ["P1"]}),
            "commodities": pd.DataFrame({"commodity": ["C1"]}),
        },
    )()

    def fake_generate(_tables, patched_model):
        assert list(patched_model.processes.columns) == ["process", "description"]
        assert list(patched_model.commodities.columns) == ["commodity", "description"]
        return {"ok": pd.DataFrame()}

    monkeypatch.setattr(
        "solve_times_nz.xl2times_compat._generate_topology_dictionary", fake_generate
    )
    assert "ok" in _with_optional_descriptions({}, model)


def _demand_tables(values: list[float]) -> dict[str, pd.DataFrame]:
    years = list(range(2023, 2023 + len(values)))
    return {
        Tag.drvr_table: pd.DataFrame(
            {
                "region": "NI",
                "source_filename": "ScenDem_Test",
                "year": years,
                "driver": "TEST_DRIVER",
                "value": values,
            }
        ),
        Tag.series: pd.DataFrame(
            {"series_name": "Constant", "year": years, "value": [1.0] * len(years)}
        ),
        Tag.drvr_allocation: pd.DataFrame(
            {
                "region": ["NI"],
                "commodity": ["TEST_DEMAND"],
                "driver": ["TEST_DRIVER"],
                "calibration": ["Constant"],
                "sensitivity": ["Constant"],
            }
        ),
        Tag.fi_t: pd.DataFrame(
            {
                "region": ["NI"],
                "year": [2023],
                "attribute": ["COM_PROJ"],
                "commodity": ["TEST_DEMAND"],
                "value": [100.0],
            }
        ),
    }


def test_demand_driver_can_reach_and_remain_at_zero() -> None:
    result = _project_demands_with_zero_continuation(
        _demand_tables([1.0, 0.5, 0.0, 0.0]), 2023
    )
    assert result["value"].tolist() == [50.0, 0.0, 0.0]


def test_demand_driver_cannot_restart_after_zero() -> None:
    with pytest.raises(ValueError, match="cannot restart from zero"):
        _project_demands_with_zero_continuation(_demand_tables([1.0, 0.0, 1.0]), 2023)


def test_implied_environmental_topology_is_exported(monkeypatch) -> None:
    model = type(
        "Model",
        (),
        {
            "implied_topology": pd.DataFrame(
                {
                    "region": ["NI", "NI"],
                    "process": ["P", "P"],
                    "commodity": ["CO2", "CO2"],
                    "io": ["OUT", "OUT"],
                }
            )
        },
    )()
    monkeypatch.setattr(
        "solve_times_nz.xl2times_compat._complete_dictionary",
        lambda _model: {
            "Topology": pd.DataFrame(
                {
                    "region": ["NI"],
                    "process": ["P"],
                    "commodity": ["GAS"],
                    "io": ["OUT"],
                }
            )
        },
    )
    result = _export_implied_emission_topology(model)
    assert result["Topology"]["commodity"].tolist() == ["GAS", "CO2"]


def test_generated_residual_after_legacy_horizon_is_omitted(monkeypatch) -> None:
    tables = {
        Tag.fi_t: pd.DataFrame(
            {
                "attribute": ["PRC_RESID", "PRC_RESID", "PRC_RESID"],
                "year": [2223, 2223, 2200],
                "value": [0, 0, 0],
                "source_filename": [pd.NA, "source.xlsx", pd.NA],
            }
        )
    }
    monkeypatch.setattr(
        "solve_times_nz.xl2times_compat._apply_final_fixup",
        lambda _config, result, _model: result,
    )

    result = _drop_generated_residuals_after_legacy_horizon(None, tables, None)

    assert result[Tag.fi_t]["year"].tolist() == [2223, 2200]
    assert result[Tag.fi_t]["source_filename"].iloc[0] == "source.xlsx"
    assert pd.isna(result[Tag.fi_t]["source_filename"].iloc[1])


def test_legacy_base_biofuel_investment_costs_are_omitted(monkeypatch) -> None:
    """Match VEDA's temporary omission of base-workbook conversion costs."""
    tables = {
        Tag.fi_t: pd.DataFrame(
            {
                "attribute": ["NCAP_COST", "NCAP_COST", "ACT_COST"],
                "process": ["CT_CWODDID", "OTHER_PROCESS", "CT_CWODDID"],
                "year": [2023, 2023, 2023],
                "value": [10483, 100, 8.67],
                "source_filename": ["VT_TIMESNZ_PRI.xlsx"] * 3,
            }
        )
    }
    monkeypatch.setattr(
        "solve_times_nz.xl2times_compat._apply_final_fixup",
        lambda _config, result, _model: result,
    )

    result = _drop_generated_residuals_after_legacy_horizon(None, tables, None)

    assert result[Tag.fi_t][["attribute", "process"]].values.tolist() == [
        ["NCAP_COST", "OTHER_PROCESS"],
        ["ACT_COST", "CT_CWODDID"],
    ]


def test_generic_uc_flo_is_expanded_for_each_declared_region(monkeypatch) -> None:
    source = EmbeddedXlTable(
        Tag.uc_t,
        {"R_S": "NI, SI"},
        "UC",
        "A1",
        "test.xlsx",
        pd.DataFrame({"UC_FLO": ["G_ELC_LV"]}),
    )
    processed = EmbeddedXlTable(
        Tag.uc_t,
        {"R_S": "NI, SI"},
        "UC",
        "A1",
        "test.xlsx",
        pd.DataFrame({"region": ["NI"], "attribute": ["UC_FLO"]}),
    )
    model = type("Model", (), {"internal_regions": {"NI"}})()

    def fake_process(_config, tables, patched_model):
        assert patched_model.internal_regions == {"NI", "SI"}
        return [processed for _ in tables]

    monkeypatch.setattr(
        "solve_times_nz.xl2times_compat._process_user_constraint_tables",
        fake_process,
    )
    result = _expand_multi_region_user_constraints(None, [source], model)

    assert result[0].dataframe["region"].tolist() == ["NI", "SI"]
    assert model.internal_regions == {"NI"}
