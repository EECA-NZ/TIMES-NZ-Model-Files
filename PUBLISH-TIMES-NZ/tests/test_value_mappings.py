"""Display labels use one config without changing release data."""

import polars as pl
import pytest

from publish_times_nz import app_config
from publish_times_nz.release_bundle import ReleaseBundle
from publish_times_nz.utilities import value_mappings


@pytest.fixture
def configured_labels(tmp_path, monkeypatch):
    monkeypatch.setattr(app_config, "PUBLISH_ROOT", tmp_path)
    bundle = ReleaseBundle(
        tmp_path,
        {
            "scenarios": [
                {"id": "steady", "label": "Baseline"},
                {"id": "shift", "label": "Transition"},
                {"id": "unknown", "label": "unknown"},
            ]
        },
    )
    monkeypatch.setattr(app_config, "configured_bundle", lambda: bundle)
    (tmp_path / "explorer_bundle.toml").write_text(
        'release = "test"\n[column_value_mappings.Scenario]\nsteady = "Steady"\n'
        '[column_value_mappings.Region]\nNI = "North Island"\n',
        encoding="utf-8",
    )
    value_mappings.load_column_value_mappings.cache_clear()
    yield tmp_path
    value_mappings.load_column_value_mappings.cache_clear()


@pytest.mark.parametrize("lazy", [False, True])
def test_selectors_and_frames_share_labels_with_manifest_fallback(
    configured_labels, lazy
):
    source = pl.DataFrame(
        {
            "Scenario": ["steady", "shift", "unknown"],
            "Region": ["NI", "NI", "elsewhere"],
            "Value": [1.0, 2.0, 3.0],
        }
    )
    mapped = value_mappings.apply_value_mappings_pl(source.lazy() if lazy else source)
    if lazy:
        mapped = mapped.collect()

    choices = value_mappings.get_choice_labels("Scenario", source["Scenario"].to_list())
    assert choices == {"steady": "Steady", "shift": "Transition", "unknown": "unknown"}
    assert mapped["Scenario"].to_list() == list(choices.values())
    assert value_mappings.apply_value_mappings_pd(source.to_pandas())[
        "Scenario"
    ].tolist() == list(choices.values())
    assert value_mappings.remap_values("Scenario", list(choices)) == list(
        choices.values()
    )
    assert mapped["Region"].to_list() == ["North Island", "North Island", "elsewhere"]
    assert source["Scenario"].to_list() == ["steady", "shift", "unknown"]
    assert mapped["Value"].to_list() == source["Value"].to_list()
