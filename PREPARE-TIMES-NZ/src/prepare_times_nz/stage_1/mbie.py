"""Pure transformations for MBIE stage-1 source tables."""

import pandas as pd


def extract_unallocated_onsite_generation(raw: pd.DataFrame) -> pd.DataFrame:
    """Return the annual PJ series from the labelled electricity-workbook row."""
    headers = raw.eq("Calendar year")
    locations = list(zip(*headers.to_numpy().nonzero()))
    if len(locations) != 1:
        raise ValueError(f"Expected one Calendar year header; found {len(locations)}")

    header_row, label_column = locations[0]
    years = pd.to_numeric(raw.iloc[header_row], errors="coerce")
    year_columns = years[years.notna() & years.ge(1900)].index
    labels = raw.iloc[:, label_column].astype(str).str.strip()
    # The actual- and estimated-sales sections repeat this row and must agree.
    values = raw.loc[labels.eq("Unallocated Onsite Generation"), year_columns].apply(
        pd.to_numeric, errors="coerce"
    )
    if values.empty:
        raise ValueError(
            "Could not find 'Unallocated Onsite Generation' in the electricity workbook"
        )
    if values.nunique(dropna=True).gt(1).any():
        raise ValueError("Conflicting 'Unallocated Onsite Generation' rows")

    result = pd.DataFrame(
        {"Year": years[year_columns].astype(int), "Value": values.iloc[0].to_numpy()}
    ).dropna(subset=["Value"])
    if 2023 not in result["Year"].values:
        raise ValueError(
            "Unallocated onsite generation does not contain the 2023 base year"
        )
    result["Unit"] = "PJ"
    return result.reset_index(drop=True)


def extract_annual_table(
    raw_df: pd.DataFrame, table_name: str, column_map: dict[str, str]
) -> pd.DataFrame:
    """Extract a labelled annual MBIE table without relying on sheet positions."""
    year_headers = raw_df.isin(["Calendar Year", "Year End"])
    locations = list(zip(*year_headers.to_numpy().nonzero()))
    if len(locations) != 1:
        raise ValueError(
            f"Expected one Calendar Year or Year End header in {table_name}; "
            f"found {len(locations)}."
        )

    header_row, year_col = locations[0]
    labels = raw_df.iloc[header_row + 1]
    selected = {"Year": year_col}
    for source, output in column_map.items():
        matches = labels[labels == source].index.tolist()
        if len(matches) != 1:
            raise ValueError(
                f"Expected one {source!r} column in {table_name}; found {len(matches)}."
            )
        selected[output] = matches[0]

    df = raw_df.iloc[header_row + 2 :, list(selected.values())].copy()
    df.columns = selected.keys()
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df = df.dropna(subset=["Year"])
    df["Year"] = df["Year"].astype(int)
    if 2023 not in df["Year"].values:
        raise ValueError(f"{table_name} does not contain the 2023 base year.")
    return df


def select_gas_balance_category(df: pd.DataFrame, category: str) -> pd.DataFrame:
    """Select one labelled row from the MBIE gas balance table."""
    labels = (
        df["Calendar year"].astype(str).str.strip().str.replace(r"\d+$", "", regex=True)
    )
    selected = df.loc[labels == category].copy()
    if len(selected) != 1:
        raise ValueError(
            f"Expected one gas balance row for {category!r}; found {len(selected)}."
        )
    return selected
