"""
Package all outputs to zipped csv for easy use
"""

import zipfile

import pandas as pd
from times_nz_internal_qa.utilities.filepaths import DATA, FINAL_DATA


def package_outputs(input_dir, output_file):
    """
    Reads every .parquet file in a directory
    and outputs a zip file to output_file
    """

    with zipfile.ZipFile(output_file, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for file in input_dir.glob("*.parquet"):
            # Read parquet
            df = pd.read_parquet(file)

            # Convert file name
            csv_name = file.with_suffix(".csv").name

            # Save CSV to a temporary string (no disk write required)
            csv_bytes = df.to_csv(index=False).encode("utf-8")

            # Write into the ZIP under its CSV name
            z.writestr(csv_name, csv_bytes)


def main():
    """
    Entrypoint
    """
    package_outputs(FINAL_DATA, DATA / "times_nz_3_wip_all_results.zip")


if __name__ == "__main__":
    main()
