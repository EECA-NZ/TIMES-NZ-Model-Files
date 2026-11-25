"""Export prepared SOLVE summary tables from one named release."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import pandas as pd

from publish_times_nz.release_bundle import ReleaseBundle


def read_summary_csv(path: Path) -> pd.DataFrame:
    """Read summary numbers explicitly, preserving text labels and undefined values."""
    frame = pd.read_csv(
        path,
        dtype=defaultdict(
            lambda: str, Value="float64", Period="int64", TimeSliceOrder="int64"
        ),
        keep_default_na=False,
        na_values={"Value": [""]},
        float_precision="round_trip",
    )
    if not {"Scenario", "Value"} <= set(frame) or frame.Scenario.eq("").any():
        raise ValueError(f"Expected summary Scenario IDs and numeric Value: {path}")
    if frame.Value.abs().eq(float("inf")).any():
        raise ValueError(f"Expected finite or undefined summary values: {path}")
    return frame


def export_summaries(
    bundle: ReleaseBundle, output: Path, scenarios: list[str] | None = None
) -> list[Path]:
    """Write labelled publication CSVs without recalculating summary values."""
    labels = {entry["id"]: entry["label"] for entry in bundle.scenarios}
    selected = list(labels) if scenarios is None else scenarios
    if not selected or set(selected) - labels.keys():
        raise ValueError("Select scenario IDs declared in the release manifest")
    sources = sorted((bundle.path / "summaries").rglob("*.csv"))
    if not sources:
        raise ValueError(f"Release contains no summaries: {bundle.path}")
    if output.resolve().is_relative_to(bundle.path.resolve()):
        raise ValueError("Summary exports must be outside the source release")
    output.mkdir(parents=True, exist_ok=False)
    written = []
    for source in sources:
        frame = read_summary_csv(source)
        if not set(frame.Scenario) <= labels.keys():
            raise ValueError(f"Undeclared summary scenarios: {source}")
        frame = frame.loc[frame.Scenario.isin(selected)].copy()
        if frame.empty:
            continue
        frame["Scenario"] = frame.Scenario.map(labels)
        destination = output / source.relative_to(bundle.path / "summaries")
        destination.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(destination, index=False)
        written.append(destination)
    (output / "summary-export-manifest.json").write_text(
        json.dumps(
            {
                "release_path": str(bundle.path.resolve()),
                "release_manifest": bundle.manifest,
                "scenario_ids": selected,
                "files": [path.relative_to(output).as_posix() for path in written],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return written
