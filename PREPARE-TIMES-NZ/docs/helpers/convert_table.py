"""
This module is not part of any workflow,
but is used to convert word tables into myst markdown

The intention is this just supports word/md conversion for now

Copy a table into a csv, then let this function read and convert

It's probably possible to expand this method,
allowing documentation to directly update with our actual input tables
"""

import csv

from prepare_times_nz.utilities.filepaths import PREP_LOCATION


def write_md_table(filepath):
    """
    Ingests a table as a csv

    Prints to console that table formatted for myst markdown
    """
    with filepath.open(newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)

    print("```{list-table} TABLE TITLE")
    print(":header-rows: 1")
    print(":name: insert-table-name-here")

    for row in rows:
        cells = "\n  - ".join(row)
        print(f"* - {cells}")

    print("```")


table = PREP_LOCATION / "docs/helpers/table_to_convert.csv"

write_md_table(table)
