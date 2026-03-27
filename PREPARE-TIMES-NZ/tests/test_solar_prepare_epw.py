"""Tests for NIWA EPW archive preparation."""

import importlib.util
import json
import tarfile
from pathlib import Path


def load_solar_prepare_epw():
    """
    Load the script module directly from its path for test usage.
    """
    module_path = (
        Path(__file__).resolve().parents[1]
        / "scripts/stage_3_scenarios/electricity/solar_prepare_epw.py"
    )
    spec = importlib.util.spec_from_file_location("solar_prepare_epw", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_prepare_epw_files_can_extract_from_tar_gz(tmp_path):
    """
    Prepared EPW files should be extracted from a committed tar.gz bundle.
    """
    module = load_solar_prepare_epw()
    archive_path = tmp_path / "tmy2_epw.tar.gz"
    archive_source_dir = tmp_path / "source"
    archive_source_dir.mkdir()
    epw_source = archive_source_dir / "TMY_NZ_AK.epw"
    epw_source.write_text(
        "\n".join(
            [
                "LOCATION,Auckland,Auckland,New Zealand,TMY2 NIWA,0,0,0,0,0",
                "DESIGN CONDITIONS,0",
                "TYPICAL/EXTREME PERIODS,0",
                "GROUND TEMPERATURES,0",
                "HOLIDAYS/DAYLIGHT SAVING,No,0,0,0",
                "COMMENTS 1,Test",
                "COMMENTS 2,Test",
                "DATA PERIODS,1,1,TMY2 Year,Sunday,1,365",
                "2007,01,01,01,60",
            ]
        ),
        encoding="utf-8",
    )
    with tarfile.open(archive_path, "w:gz") as handle:
        handle.add(epw_source, arcname="tmy2_epw/TMY_NZ_AK.epw")

    prepared_dir = tmp_path / "prepared_epw"
    metadata_dir = tmp_path / "metadata"
    module.PREFERRED_EPW_DIR = tmp_path / "missing"
    module.PREFERRED_EPW_ARCHIVE = archive_path
    module.PREPARED_EPW_DIR = prepared_dir
    module.PREPARED_EPW_SENTINEL = prepared_dir / ".prepared"
    module.METADATA_DIR = metadata_dir

    module.prepare_epw_files()

    extracted = prepared_dir / "TMY_NZ_AK.epw"
    assert extracted.exists()
    assert module.PREPARED_EPW_SENTINEL.exists()

    summary = json.loads((metadata_dir / "prepare_epw_summary.json").read_text())
    assert summary["source_type"] == "archive"
    assert summary["source_path"] == str(archive_path)
    assert summary["copied_files"] == 1
