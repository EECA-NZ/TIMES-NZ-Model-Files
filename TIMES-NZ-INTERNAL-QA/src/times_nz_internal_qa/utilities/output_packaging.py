"""Package already-produced QA outputs for download."""

import io
import zipfile

import pandas as pd
from times_nz_internal_qa.utilities.value_mappings import apply_value_mappings_pd


def build_outputs_zip_bytes(input_dir):
    """Build the full-results zip in memory from parquet outputs."""
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for file in input_dir.glob("*.parquet"):
            df = pd.read_parquet(file)
            df = apply_value_mappings_pd(df)

            csv_name = file.with_suffix(".csv").name
            csv_bytes = df.to_csv(index=False).encode("utf-8")
            z.writestr(csv_name, csv_bytes)

    return zip_buffer.getvalue()
