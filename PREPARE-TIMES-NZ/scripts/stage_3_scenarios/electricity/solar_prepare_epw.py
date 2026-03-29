"""
Prepare NIWA EPW files for the solar availability-factor workflow.
"""

from __future__ import annotations

import csv
import json
import shutil
import tarfile

from prepare_times_nz.utilities.filepaths import DATA_RAW, STAGE_3_DATA

PREFERRED_EPW_DIR = DATA_RAW / "external_data/niwa/tmy2_epw"
PREFERRED_EPW_ARCHIVE = DATA_RAW / "external_data/niwa/tmy2_epw.tar.gz"

OUTPUT_ROOT = STAGE_3_DATA / "electricity/solar_af"
PREPARED_EPW_DIR = OUTPUT_ROOT / "prepared_epw"
PREPARED_EPW_SENTINEL = PREPARED_EPW_DIR / ".prepared"
METADATA_DIR = OUTPUT_ROOT / "metadata"


def ensure_output_dir(path):
    """
    Create an output directory with predictable permissions.
    """
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(0o755)
    return path


def resolve_epw_source():
    """
    Locate the NIWA EPW bundle.
    """
    if PREFERRED_EPW_DIR.exists() and any(PREFERRED_EPW_DIR.glob("*.epw")):
        return {
            "source_type": "directory",
            "source_path": PREFERRED_EPW_DIR,
        }

    if PREFERRED_EPW_ARCHIVE.exists():
        return {
            "source_type": "archive",
            "source_path": PREFERRED_EPW_ARCHIVE,
        }

    raise FileNotFoundError(
        "No NIWA EPW source found. Expected either "
        f"{PREFERRED_EPW_DIR} or {PREFERRED_EPW_ARCHIVE}."
    )


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


def normalize_epw(path):
    """
    Normalize EPW hour fields only when a file actually uses 00..23 notation.
    """
    rows = read_epw_rows(path)
    needs_normalization = any(
        len(row) >= 5 and row[4].strip() == "60" and row[3].strip() == "00"
        for row in rows[8:]
    )
    if not needs_normalization:
        return False

    changed = False
    for row in rows[8:]:
        if len(row) < 5:
            continue
        hour = row[3].strip()
        minute = row[4].strip()
        if minute == "60" and hour.isdigit():
            hour_int = int(hour)
            if 0 <= hour_int <= 23:
                normalized = str(hour_int + 1).zfill(2)
                if normalized != row[3]:
                    row[3] = normalized
                    changed = True

    if changed:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerows(rows)

    return changed


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


def copy_epw_bundle(source, output_dir):
    """
    Copy or extract the NIWA EPW bundle into stage-3 storage.
    """
    source_type = source["source_type"]
    source_path = source["source_path"]
    copied = 0
    normalized = 0

    if source_type == "directory":
        source_paths = sorted(source_path.glob("*.epw"))
        for epw_path in source_paths:
            target_path = output_dir / epw_path.name
            shutil.copy2(epw_path, target_path)
            copied += 1
            if normalize_epw(target_path):
                normalized += 1
        return copied, normalized

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
                if normalize_epw(target_path):
                    normalized += 1
        return copied, normalized

    raise ValueError(f"Unsupported EPW source type {source_type!r}.")


def prepare_epw_files():
    """
    Copy bundled EPWs into stage-3 storage and normalize them in place.
    """
    source = resolve_epw_source()
    output_dir = ensure_output_dir(PREPARED_EPW_DIR)
    copied, normalized = copy_epw_bundle(source, output_dir)

    PREPARED_EPW_SENTINEL.touch()
    ensure_output_dir(METADATA_DIR)
    with (METADATA_DIR / "prepare_epw_summary.json").open(
        "w", encoding="utf-8"
    ) as handle:
        json.dump(
            {
                "source_type": source["source_type"],
                "source_path": str(source["source_path"]),
                "copied_files": copied,
                "normalized_files": normalized,
            },
            handle,
            indent=2,
        )


if __name__ == "__main__":
    prepare_epw_files()
