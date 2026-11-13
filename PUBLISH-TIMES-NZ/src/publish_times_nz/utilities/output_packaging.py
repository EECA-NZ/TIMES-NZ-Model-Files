"""Package already-produced QA outputs for download."""

import io
import zipfile

import pandas as pd
from publish_times_nz.utilities.value_mappings import apply_value_mappings_pd


def build_outputs_zip_bytes(parquet_files):
    """Build the full-results zip in memory from parquet outputs."""
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for file in parquet_files:
            df = pd.read_parquet(file)
            df = apply_value_mappings_pd(df)

            csv_name = file.with_suffix(".csv").name
            csv_bytes = df.to_csv(index=False).encode("utf-8")
            z.writestr(csv_name, csv_bytes)

    return zip_buffer.getvalue()
