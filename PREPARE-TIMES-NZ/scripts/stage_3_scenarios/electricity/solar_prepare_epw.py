"""
Prepare NIWA EPW files for the solar availability-factor workflow.
"""

from __future__ import annotations

import csv
import json
import re
import shutil
import tarfile
from pathlib import Path

from prepare_times_nz.utilities.filepaths import DATA_RAW, STAGE_3_DATA

NIWA_DATA_DIR = DATA_RAW / "external_data/niwa"

OUTPUT_ROOT = STAGE_3_DATA / "electricity/solar_af"
PREPARED_EPW_DIR = OUTPUT_ROOT / "prepared_epw"
PREPARED_EPW_SENTINEL = PREPARED_EPW_DIR / ".prepared"
METADATA_DIR = OUTPUT_ROOT / "metadata"

EXPECTED_ZONES = {
    "AK",
    "BP",
    "CC",
    "DN",
    "EC",
    "HN",
    "IN",
    "MW",
    "NL",
    "NM",
    "NP",
    "OC",
    "QL",
    "RR",
    "TP",
    "WC",
    "WI",
    "WN",
}

EPW_FILENAME_PATTERNS = (re.compile(r"^TMY3_NZ_(?P<zone>[A-Z]{2})\.epw$"),)

SOURCE_CANDIDATE = ("TMY3", "archive", NIWA_DATA_DIR / "tmy3_epw.tar.gz")


def ensure_output_dir(path):
    """
    Create an output directory with predictable permissions.
    """
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(0o755)
    return path


def extract_zone_code(filename: str) -> str | None:
    """
    Return the NIWA climate-zone code from a supported EPW filename.
    """
    for pattern in EPW_FILENAME_PATTERNS:
        match = pattern.match(filename)
        if match:
            return match.group("zone")
    return None


def resolve_epw_source():
    """
    Locate the preferred NIWA EPW bundle.
    """
    dataset, source_type, source_path = SOURCE_CANDIDATE
    if source_path.exists():
        return {
            "dataset": dataset,
            "source_type": source_type,
            "source_path": source_path,
        }

    raise FileNotFoundError("No NIWA EPW source found. Checked: " f"{source_path}.")


def read_epw_rows(epw_path):
    """
    Read an EPW file using the encodings present in the NIWA datasets.
    """
    try:
        with epw_path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.reader(handle))
    except UnicodeDecodeError:
        with epw_path.open("r", encoding="latin-1", newline="") as handle:
            return list(csv.reader(handle))


def validate_epw_file(path: Path):
    """
    Validate filename and hour-field conventions for a NIWA EPW file.
    """
    zone = extract_zone_code(path.name)
    if zone is None:
        raise ValueError(
            f"Unsupported NIWA EPW filename {path.name}. Expected TMY3_NZ_<zone>.epw."
        )

    rows = read_epw_rows(path)
    data_rows = rows[8:]
    if len(data_rows) != 8760:
        raise ValueError(f"Expected 8760 EPW rows in {path}, found {len(data_rows)}")

    for row_num, row in enumerate(data_rows, start=9):
        if len(row) < 5:
            raise ValueError(
                f"EPW data row {row_num} has fewer than 5 columns in {path}"
            )

        hour = row[3].strip()
        minute = row[4].strip()
        if minute not in {"0", "60"}:
            raise ValueError(
                f"Unsupported EPW minute value {minute!r} at row {row_num} in {path}. "
                "The workflow expects NIWA EPW minute values of 0 or 60."
            )
        if not hour.isdigit() or not 1 <= int(hour) <= 24:
            raise ValueError(
                f"Unsupported EPW hour value {hour!r} at row {row_num} in {path}. "
                "The workflow now validates EPW-standard 01..24 hours instead of "
                "normalizing 00..23 values."
            )

    return zone


def _archive_members(archive_path):
    """
    Return the EPW members from the NIWA archive.
    """
    with tarfile.open(archive_path, "r:gz") as handle:
        members = [member for member in handle.getmembers() if member.isfile()]
        epw_members = [member for member in members if member.name.endswith(".epw")]

    if not epw_members:
        raise FileNotFoundError(f"No .epw files found in archive {archive_path}.")

    return sorted(epw_members, key=lambda member: member.name)


def clear_prepared_epw_dir(output_dir: Path):
    """
    Remove previously prepared EPW files so stale bundles cannot linger.
    """
    for epw_path in output_dir.glob("*.epw"):
        epw_path.unlink()


def copy_epw_bundle(source, output_dir):
    """
    Copy or extract the NIWA EPW bundle into stage-3 storage.
    """
    source_type = source["source_type"]
    source_path = source["source_path"]
    copied = 0
    copied_paths = []

    if source_type == "archive":
        with tarfile.open(source_path, "r:gz") as handle:
            for member in _archive_members(source_path):
                extracted = handle.extractfile(member)
                if extracted is None:
                    raise FileNotFoundError(
                        f"Could not extract {member.name} from {source_path}."
                    )
                target_path = output_dir / member.name.rsplit("/", maxsplit=1)[-1]
                with target_path.open("wb") as output_handle:
                    shutil.copyfileobj(extracted, output_handle)
                copied += 1
                copied_paths.append(target_path)
        return copied, copied_paths

    raise ValueError(f"Unsupported EPW source type {source_type!r}.")


def validate_prepared_bundle(epw_paths: list[Path]):
    """
    Validate that the prepared bundle contains exactly the supported 18 zones.
    """
    zone_to_file = {}
    for epw_path in sorted(epw_paths):
        zone = validate_epw_file(epw_path)
        existing = zone_to_file.get(zone)
        if existing is not None:
            raise ValueError(
                f"Duplicate EPW files for zone {zone}: {existing.name} and {epw_path.name}"
            )
        zone_to_file[zone] = epw_path.name

    missing = sorted(EXPECTED_ZONES.difference(zone_to_file))
    if missing:
        raise ValueError(f"Missing EPW files for zones: {', '.join(missing)}")

    extra = sorted(set(zone_to_file).difference(EXPECTED_ZONES))
    if extra:
        raise ValueError(f"Unexpected EPW zones: {', '.join(extra)}")

    return zone_to_file


def prepare_epw_files():
    """
    Copy NIWA EPWs into stage-3 storage and validate them in place.
    """
    source = resolve_epw_source()
    output_dir = ensure_output_dir(PREPARED_EPW_DIR)
    clear_prepared_epw_dir(output_dir)
    copied, copied_paths = copy_epw_bundle(source, output_dir)
    zone_to_file = validate_prepared_bundle(copied_paths)

    PREPARED_EPW_SENTINEL.touch()
    ensure_output_dir(METADATA_DIR)
    with (METADATA_DIR / "prepare_epw_summary.json").open(
        "w", encoding="utf-8"
    ) as handle:
        json.dump(
            {
                "dataset": source["dataset"],
                "source_type": source["source_type"],
                "source_path": str(source["source_path"]),
                "copied_files": copied,
                "prepared_files": sorted(path.name for path in copied_paths),
                "zones": [
                    {"ZoneCode": zone, "EPWFile": zone_to_file[zone]}
                    for zone in sorted(zone_to_file)
                ],
            },
            handle,
            indent=2,
        )


if __name__ == "__main__":
    prepare_epw_files()
