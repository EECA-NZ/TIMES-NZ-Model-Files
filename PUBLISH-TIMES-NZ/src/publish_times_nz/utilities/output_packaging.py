"""Package prepared release outputs for download."""

import io
import zipfile

import pandas as pd

from publish_times_nz.reporting import read_summary_csv
from publish_times_nz.utilities.value_mappings import apply_value_mappings_pd


def build_outputs_zip_bytes(result_files):
    """Build the full-results zip from Parquets and prepared summary CSVs."""
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for file in result_files:
            if file.suffix == ".csv":
                df = read_summary_csv(file)
                summary_root = next(p for p in file.parents if p.name == "summaries")
                csv_name = file.relative_to(summary_root.parent).as_posix()
            else:
                df = pd.read_parquet(file)
                csv_name = file.with_suffix(".csv").name
            df = apply_value_mappings_pd(df)

            csv_bytes = df.to_csv(index=False).encode("utf-8")
            z.writestr(csv_name, csv_bytes)

    return zip_buffer.getvalue()
