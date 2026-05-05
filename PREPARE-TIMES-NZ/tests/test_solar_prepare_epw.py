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


def write_test_epw(path: Path, hour: str = "01", minute: str = "0"):
    """
    Write a minimal synthetic EPW file.
    """
    path.write_text(
        "\n".join(
            [
                "LOCATION,Auckland,Auckland,New Zealand,TMY3 NIWA,0,0,0,0,0",
                "DESIGN CONDITIONS,0",
                "TYPICAL/EXTREME PERIODS,0",
                "GROUND TEMPERATURES,0",
                "HOLIDAYS/DAYLIGHT SAVING,No,0,0,0",
                "COMMENTS 1,Test",
                "COMMENTS 2,Test",
                "DATA PERIODS,1,1,TMY3 Year,Sunday,1,365",
            ]
            + [f"2024,01,01,{hour},{minute}"] * 8760
        ),
        encoding="utf-8",
    )


def test_prepare_epw_files_can_extract_from_tar_gz(tmp_path):
    """
    Prepared EPW files should be extracted from a committed TMY3 tar.gz bundle.
    """
    module = load_solar_prepare_epw()
    archive_path = tmp_path / "tmy3_epw.tar.gz"
    archive_source_dir = tmp_path / "source"
    archive_source_dir.mkdir()
    for zone in sorted(module.EXPECTED_ZONES):
        write_test_epw(archive_source_dir / f"TMY3_NZ_{zone}.epw")
    with tarfile.open(archive_path, "w:gz") as handle:
        for epw_source in sorted(archive_source_dir.glob("*.epw")):
            handle.add(epw_source, arcname=f"tmy3_epw/{epw_source.name}")

    prepared_dir = tmp_path / "prepared_epw"
    metadata_dir = tmp_path / "metadata"
    module.SOURCE_CANDIDATE = ("TMY3", "archive", archive_path)
    module.PREPARED_EPW_DIR = prepared_dir
    module.PREPARED_EPW_SENTINEL = prepared_dir / ".prepared"
    module.METADATA_DIR = metadata_dir

    module.prepare_epw_files()

    extracted = prepared_dir / "TMY3_NZ_AK.epw"
    assert extracted.exists()
    assert module.PREPARED_EPW_SENTINEL.exists()

    summary = json.loads((metadata_dir / "prepare_epw_summary.json").read_text())
    assert summary["dataset"] == "TMY3"
    assert summary["source_type"] == "archive"
    assert summary["source_path"] == str(archive_path)
    assert summary["copied_files"] == len(module.EXPECTED_ZONES)
    assert len(summary["zones"]) == len(module.EXPECTED_ZONES)


def test_prepare_epw_files_rejects_non_epw_hour_conventions(tmp_path):
    """
    Files using 00..23 hour notation should fail validation instead of being rewritten.
    """
    module = load_solar_prepare_epw()
    archive_source_dir = tmp_path / "source"
    archive_source_dir.mkdir()
    for zone in sorted(module.EXPECTED_ZONES):
        hour = "00" if zone == "AK" else "01"
        write_test_epw(archive_source_dir / f"TMY3_NZ_{zone}.epw", hour=hour)

    archive_path = tmp_path / "tmy3_epw.tar.gz"
    with tarfile.open(archive_path, "w:gz") as handle:
        for epw_source in sorted(archive_source_dir.glob("*.epw")):
            handle.add(epw_source, arcname=f"tmy3_epw/{epw_source.name}")

    module.SOURCE_CANDIDATE = ("TMY3", "archive", archive_path)
    module.PREPARED_EPW_DIR = tmp_path / "prepared_epw"
    module.PREPARED_EPW_SENTINEL = module.PREPARED_EPW_DIR / ".prepared"
    module.METADATA_DIR = tmp_path / "metadata"

    try:
        module.prepare_epw_files()
        raise AssertionError("Expected invalid hour convention to raise")
    except ValueError as exc:
        assert "validates EPW-standard 01..24 hours" in str(exc)


def test_prepare_epw_files_accepts_supported_niwa_minute_conventions(tmp_path):
    """
    Validation should accept both minute 60 and MBIE TMY3 minute 0 files.
    """
    module = load_solar_prepare_epw()
    archive_source_dir = tmp_path / "source"
    archive_source_dir.mkdir()
    for zone in sorted(module.EXPECTED_ZONES):
        minute = "60" if zone == "AK" else "0"
        write_test_epw(archive_source_dir / f"TMY3_NZ_{zone}.epw", minute=minute)

    archive_path = tmp_path / "tmy3_epw.tar.gz"
    with tarfile.open(archive_path, "w:gz") as handle:
        for epw_source in sorted(archive_source_dir.glob("*.epw")):
            handle.add(epw_source, arcname=f"tmy3_epw/{epw_source.name}")

    module.SOURCE_CANDIDATE = ("TMY3", "archive", archive_path)
    module.PREPARED_EPW_DIR = tmp_path / "prepared_epw"
    module.PREPARED_EPW_SENTINEL = module.PREPARED_EPW_DIR / ".prepared"
    module.METADATA_DIR = tmp_path / "metadata"

    module.prepare_epw_files()

    assert (module.PREPARED_EPW_DIR / "TMY3_NZ_AK.epw").exists()
