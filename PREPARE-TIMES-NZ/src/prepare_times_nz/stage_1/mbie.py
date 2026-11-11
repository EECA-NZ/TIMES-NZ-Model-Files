"""Pure transformations for MBIE stage-1 source tables."""

import pandas as pd


def tidy_energy_balance(data: pd.DataFrame) -> pd.DataFrame:
    """Standardise MBIE's machine-readable annual Energy Balance table."""
    required = {"entry", "fuel", "year", "unit", "value"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(
            "Energy Balance data is missing columns: " + ", ".join(sorted(missing))
        )
    return data.rename(
        columns={
            "entry": "Entry",
            "fuel": "Fuel",
            "year": "Year",
            "unit": "Unit",
            "value": "Value",
        }
    )[["Entry", "Fuel", "Year", "Unit", "Value"]]


def tidy_annual_electricity(
    data: pd.DataFrame,
    row_slice: slice,
    category_name: str,
    unit: str,
    variable_name: str,
) -> pd.DataFrame:
    """Select and reshape one annual electricity generation table."""
    df = data.iloc[row_slice].copy().drop(columns="Annual % change")
    df = df.rename(columns={"Calendar year": category_name})
    df[category_name] = df[category_name].str.replace(r"\d+$", "", regex=True)
    df["Unit"] = unit
    df["Variable"] = variable_name
    return pd.melt(
        df,
        id_vars=[category_name, "Unit", "Variable"],
        var_name="Year",
        value_name="Value",
    ).rename(columns={category_name: "FuelType"})


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


def extract_electricity_demand_totals(raw: pd.DataFrame) -> pd.DataFrame:
    """Return the labelled calculated and observed demand series from MBIE."""
    year_headers = pd.to_numeric(raw.iloc[4], errors="coerce")
    year_columns = year_headers[year_headers.notna() & year_headers.ge(1900)].index

    calculated = raw.iloc[
        raw.iloc[:, 0]
        .eq("Total Electricity Demand (Calculated)")
        .to_numpy()
        .nonzero()[0]
    ]
    observed = raw.iloc[
        raw.iloc[:, 1]
        .astype(str)
        .str.replace(r"\d+$", "", regex=True)
        .eq("Total Electricity Demand (Observed)")
        .to_numpy()
        .nonzero()[0]
    ]
    if len(calculated) != 1 or len(observed) != 1:
        raise ValueError(
            "Could not find unique calculated and observed electricity demand rows"
        )

    result = pd.DataFrame(
        {
            "Year": year_headers[year_columns].astype(int),
            "CalculatedDemandGWh": pd.to_numeric(
                calculated.iloc[0, year_columns], errors="raise"
            ).to_numpy(),
            "ObservedDemandGWh": pd.to_numeric(
                observed.iloc[0, year_columns], errors="raise"
            ).to_numpy(),
        }
    )
    return result


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


def tidy_generation_by_fuel(raw: pd.DataFrame) -> pd.DataFrame:
    """Format electricity-only generation by fuel in GWh."""
    df = extract_annual_table(
        raw,
        "electricity generation by fuel",
        {
            "Hydro": "Hydro",
            "Geo- thermal": "Geothermal",
            "Biogas": "Biogas",
            "Wind": "Wind",
            "Solar PV": "Solar PV",
            "Oil1": "Oil",
            "Coal": "Coal",
            "Gas": "Gas",
        },
    ).melt(id_vars="Year", var_name="Fuel", value_name="Value")
    df["Unit"] = "GWh"
    df["Variable"] = "Electricity generation (no cogen)"
    return df.rename(columns={"Fuel": "FuelType"})


def tidy_generation_capacity(raw: pd.DataFrame) -> pd.DataFrame:
    """Format installed generation capacity by technology in MW."""
    df = extract_annual_table(
        raw,
        "generation capacity by plant type",
        {
            "Hydro": "Hydro",
            "Geothermal": "Geothermal",
            "Biogas": "Biogas",
            "Wind": "Wind",
            "Solar PV": "Solar PV",
            "Diesel": "Diesel",
            "Coal/Gas": "Coal/Gas",
            "Gas": "Gas",
            "Other Thermal2": "Other electricity generation",
            "Gas3": "Gas Cogen",
            "Other4": "Other Cogen",
        },
    ).melt(id_vars="Year", var_name="Technology", value_name="Value")
    df["Value"] = pd.to_numeric(df["Value"], errors="raise").fillna(0)
    df["Unit"] = "MW"
    df["Variable"] = "Electricity generation capacity at end year"
    return df


def tidy_gas_balance_category(
    data: pd.DataFrame, category: str, category_name: str, unit: str, variable_name: str
) -> pd.DataFrame:
    """Select and reshape one labelled category from MBIE's annual gas balance."""
    df = data.copy()
    df.columns = [col.strip() if isinstance(col, str) else col for col in df.columns]
    df = select_gas_balance_category(df, category).rename(
        columns={"Calendar year": category_name}
    )
    df[category_name] = df[category_name].str.replace(r"\d+$", "", regex=True)
    df["Unit"] = unit
    df["Variable"] = variable_name
    return pd.melt(
        df,
        id_vars=[category_name, "Unit", "Variable"],
        var_name="Year",
        value_name="Value",
    ).dropna(subset=["Value"])


def tidy_production_profile(data: pd.DataFrame, label: str) -> pd.DataFrame:
    """Reshape an MBIE petroleum-reserves production profile to long form."""
    df = pd.melt(data, id_vars="Field", var_name="Year", value_name="Value")
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce").fillna(0)
    df["Unit"] = "PJ"
    df["Variable"] = label
    return df


def tidy_contingent_reserves(data: pd.DataFrame) -> pd.DataFrame:
    """Format MBIE's fixed-layout 2C resource table."""
    df = data.copy()
    df.columns = ["Field", "Oil", "Condensate", "LPG", "Natural gas"]
    df = df.melt(id_vars="Field", var_name="Fuel", value_name="Value")
    df["Unit"] = df["Fuel"].map(
        {
            "Oil": "Million Barrels",
            "Condensate": "Million Barrels",
            "LPG": "kt",
            "Natural gas": "PJ",
        }
    )
    return df
