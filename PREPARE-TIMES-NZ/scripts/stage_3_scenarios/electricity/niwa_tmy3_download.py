#!/usr/bin/env python3
"""
Download the public NIWA/MBIE present-climate TMY3 ZIP and convert it to tar.gz.

The repo stores the committed dataset as:
- data_raw/external_data/niwa/tmy3_epw.tar.gz

Examples
--------
python \
  PREPARE-TIMES-NZ/scripts/stage_3_scenarios/electricity/niwa_tmy3_download.py
python \
  PREPARE-TIMES-NZ/scripts/stage_3_scenarios/electricity/niwa_tmy3_download.py \
  --zip-path /path/to/tmy3.zip
python \
  PREPARE-TIMES-NZ/scripts/stage_3_scenarios/electricity/niwa_tmy3_download.py \
  --tar-path ./tmy3_epw.tar.gz --keep-zip
"""

from __future__ import annotations

import argparse
import io
import re
import sys
import tarfile
import zipfile
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

WEATHER_PAGE_URL = (
    "https://www.building.govt.nz/getting-started/"
    "climate-change-work-programme/resources/weather-files-aotearoa-new-zealand"
)

KNOWN_TMY3_ZIP_URL = (
    "https://www.building.govt.nz/assets/Uploads/getting-started/"
    "building-for-climate-change/Weather-files-ZIP-files/tmy3.zip"
)

DEFAULT_TAR_PATH = (
    Path(__file__).resolve().parents[3] / "data_raw/external_data/niwa/tmy3_epw.tar.gz"
)
DEFAULT_DOWNLOAD_ZIP_PATH = DEFAULT_TAR_PATH.parent / "tmy3_download.zip"

EXPECTED_EPW_FILENAMES = {
    "TMY3_NZ_AK.epw",
    "TMY3_NZ_BP.epw",
    "TMY3_NZ_CC.epw",
    "TMY3_NZ_DN.epw",
    "TMY3_NZ_EC.epw",
    "TMY3_NZ_HN.epw",
    "TMY3_NZ_IN.epw",
    "TMY3_NZ_MW.epw",
    "TMY3_NZ_NL.epw",
    "TMY3_NZ_NM.epw",
    "TMY3_NZ_NP.epw",
    "TMY3_NZ_OC.epw",
    "TMY3_NZ_QL.epw",
    "TMY3_NZ_RR.epw",
    "TMY3_NZ_TP.epw",
    "TMY3_NZ_WC.epw",
    "TMY3_NZ_WI.epw",
    "TMY3_NZ_WN.epw",
}

USER_AGENT = "Mozilla/5.0 (compatible; NIWA-TMY3-Downloader/1.0)"


class DownloadError(RuntimeError):
    """Raised when the weather ZIP cannot be discovered or downloaded."""


def ensure_output_dir(path: Path) -> Path:
    """Create an output directory if needed and return it."""
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(0o755)
    return path


def fetch_bytes(url: str, timeout: int = 60) -> bytes:
    """Fetch raw bytes from a URL using the helper user agent."""
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=timeout) as response:
        return response.read()


def fetch_text(url: str, timeout: int = 60) -> str:
    """Fetch decoded UTF-8 text from a URL."""
    return fetch_bytes(url, timeout=timeout).decode("utf-8", errors="replace")


def discover_tmy3_zip_url(page_url: str = WEATHER_PAGE_URL, timeout: int = 60) -> str:
    """
    Discover the current present-climate TMY3 ZIP URL from the official page.
    """
    try:
        html = fetch_text(page_url, timeout=timeout)
    except (HTTPError, URLError, TimeoutError, OSError):
        return KNOWN_TMY3_ZIP_URL

    anchor_pattern = re.compile(
        r'<a[^>]+href=["\'](?P<href>[^"\']+)["\'][^>]*>(?P<label>.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )
    for match in anchor_pattern.finditer(html):
        href = match.group("href")
        label = re.sub(r"<[^>]+>", " ", match.group("label"))
        label = re.sub(r"\s+", " ", label).strip().lower()
        if "download the tmy3 weather files for present climate" in label:
            return urljoin(page_url, href)

    href_pattern = re.compile(
        r'href=["\'](?P<href>[^"\']+tmy3\.zip)["\']', re.IGNORECASE
    )
    hrefs = [urljoin(page_url, m.group("href")) for m in href_pattern.finditer(html)]
    if hrefs:
        for href in hrefs:
            if "Weather-files-ZIP-files" in href:
                return href
        return hrefs[0]

    return KNOWN_TMY3_ZIP_URL


def download_file(
    url: str, destination: Path, timeout: int = 120, overwrite: bool = False
) -> Path:
    """Download a ZIP file to disk and verify that it is actually a ZIP."""
    if destination.exists() and not overwrite:
        print(f"Using existing ZIP: {destination}")
        return destination

    ensure_output_dir(destination.parent)
    print(f"Downloading: {url}")
    data = fetch_bytes(url, timeout=timeout)
    validation_path = destination.parent / ".tmp_validation.zip"
    validation_path.write_bytes(data)
    try:
        if not zipfile.is_zipfile(validation_path):
            raise DownloadError(
                "Downloaded content is not a ZIP file. MBIE may be blocking scripted "
                "downloads. Download the archive in a browser and rerun this script "
                "with --zip-path pointing at the local file."
            )
    finally:
        validation_path.unlink(missing_ok=True)

    destination.write_bytes(data)
    print(f"Saved ZIP: {destination} ({destination.stat().st_size:,} bytes)")
    return destination


def iter_matching_members(zf: zipfile.ZipFile) -> Iterable[zipfile.ZipInfo]:
    """Yield present-climate TMY3 EPW members from the MBIE ZIP archive."""
    for info in zf.infolist():
        if info.is_dir():
            continue
        name = Path(info.filename).name
        lower_name = name.lower()
        if not lower_name.endswith(".epw"):
            continue
        if not lower_name.startswith("tmy3_nz_"):
            continue
        if "_m1_" in lower_name or "_m2_" in lower_name or "_m3_" in lower_name:
            continue
        yield info


def extract_epw_bytes(zip_path: Path) -> list[tuple[str, bytes]]:
    """Read all supported present-climate TMY3 EPWs from a ZIP archive."""
    extracted: list[tuple[str, bytes]] = []
    with zipfile.ZipFile(zip_path) as zf:
        members = list(iter_matching_members(zf))
        if not members:
            raise DownloadError(
                f"No present-climate TMY3 EPW files were found in ZIP: {zip_path}"
            )

        for info in members:
            member_name = Path(info.filename).name
            with zf.open(info) as src:
                extracted.append((member_name, src.read()))

    return sorted(extracted, key=lambda item: item[0])


def resolve_local_zip_path(zip_path: Path) -> Path:
    """
    Validate that a user-supplied local ZIP exists before attempting conversion.
    """
    if zip_path.exists():
        return zip_path

    raise DownloadError(
        f"Local ZIP not found: {zip_path}. Check the browser download location and "
        "pass the correct path with --zip-path, or omit --zip-path to let the script "
        "attempt a direct download."
    )


def validate_extraction(files: Iterable[tuple[str, bytes]]) -> None:
    """Confirm the extracted archive contains the expected 18 EPW files."""
    found = {name for name, _ in files}
    missing = sorted(EXPECTED_EPW_FILENAMES - found)
    extra = sorted(found - EXPECTED_EPW_FILENAMES)

    print(f"\nFound {len(found)} present-climate TMY3 EPW files.")
    if missing:
        print("Missing expected files:")
        for name in missing:
            print(f"  - {name}")
    if extra:
        print("Unexpected extra files:")
        for name in extra:
            print(f"  - {name}")

    if missing:
        raise DownloadError(
            "Archive extraction did not produce the expected 18 present-climate TMY3 EPW files."
        )


def write_tar_bundle(
    tar_path: Path, files: Iterable[tuple[str, bytes]], overwrite: bool = False
) -> Path:
    """Write the validated EPW files into the committed tar.gz layout."""
    if tar_path.exists() and not overwrite:
        raise DownloadError(
            f"Tar archive already exists: {tar_path}. Use --overwrite to replace it."
        )

    ensure_output_dir(tar_path.parent)
    with tarfile.open(tar_path, "w:gz") as handle:
        for filename, contents in files:
            info = tarfile.TarInfo(name=f"tmy3_epw/{filename}")
            info.size = len(contents)
            handle.addfile(info, io.BytesIO(contents))

    print(f"Saved tar.gz: {tar_path} ({tar_path.stat().st_size:,} bytes)")
    return tar_path


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the TMY3 download helper."""
    parser = argparse.ArgumentParser(
        description=(
            "Download the 18 public NIWA/MBIE present-climate TMY3 EPW files "
            "and convert them to tar.gz."
        )
    )
    parser.add_argument(
        "--page-url",
        default=WEATHER_PAGE_URL,
        help="Official weather-files landing page to scrape for the TMY3 ZIP link.",
    )
    parser.add_argument(
        "--zip-url",
        default=None,
        help="Explicit ZIP URL to download instead of scraping the page.",
    )
    parser.add_argument(
        "--zip-path",
        type=Path,
        default=None,
        help="Optional local ZIP path to validate and convert instead of downloading.",
    )
    parser.add_argument(
        "--tar-path",
        type=Path,
        default=DEFAULT_TAR_PATH,
        help="Path where the output tar.gz archive will be written.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="HTTP timeout in seconds for page fetches and downloads.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite an existing downloaded ZIP or output tar.gz file.",
    )
    parser.add_argument(
        "--keep-zip",
        action="store_true",
        help=(
            "Keep a downloaded ZIP after conversion. Local ZIP inputs are never "
            "deleted."
        ),
    )
    return parser.parse_args()


def main() -> int:
    """Run the ZIP download or conversion workflow and write the tar.gz bundle."""
    args = parse_args()
    tar_path = args.tar_path.expanduser().resolve()
    zip_path = (
        args.zip_path.expanduser().resolve()
        if args.zip_path
        else DEFAULT_DOWNLOAD_ZIP_PATH
    )
    zip_url = args.zip_url or discover_tmy3_zip_url(
        page_url=args.page_url, timeout=args.timeout
    )
    downloaded_zip = False
    local_zip_supplied = args.zip_path is not None

    print(f"Weather page: {args.page_url}")
    print(f"ZIP URL: {zip_url}")
    print(f"Output tar.gz: {tar_path}")

    try:
        if local_zip_supplied:
            zip_path = resolve_local_zip_path(zip_path)
            print(f"Using local ZIP: {zip_path}")
        else:
            download_file(
                zip_url, zip_path, timeout=args.timeout, overwrite=args.overwrite
            )
            downloaded_zip = True

        extracted = extract_epw_bytes(zip_path)
        validate_extraction(extracted)
        write_tar_bundle(tar_path, extracted, overwrite=args.overwrite)
    except (
        HTTPError,
        URLError,
        TimeoutError,
        zipfile.BadZipFile,
        OSError,
        DownloadError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        if downloaded_zip and zip_path.exists() and not args.keep_zip:
            try:
                zip_path.unlink()
                print(f"Removed downloaded ZIP: {zip_path}")
            except OSError:
                pass

    print("\nArchived files:")
    for filename, _ in extracted:
        print(f"  - {filename}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
