"""
Functions used for data processing and transformation, and comparison of DataFrames.
"""

import re
import csv
import logging
import numpy as np
import pandas as pd

from constants import *

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def read_vd(filepath):
    """
    Reads a VD file, using column names extracted from the file's header with regex, skipping non-CSV formatted header lines.

    :param filepath: Path to the VD file.
    :param scen_label: Label for the 'scen' column for rows from this file.
    """
    dimensions_pattern = re.compile(r"\*\s*Dimensions-")

    # Determine the number of rows to skip and the column names
    with open(filepath, "r", encoding="utf-8") as file:
        columns = None
        skiprows = 0
        for line in file:
            if dimensions_pattern.search(line):
                columns_line = line.split("- ")[1].strip()
                columns = columns_line.split(";")
                continue
            if line.startswith('"'):
                break
            skiprows += 1

    # Read the CSV file with the determined column names and skiprows
    df = pd.read_csv(
        filepath, skiprows=skiprows, names=columns, header=None, low_memory=False
    )
    return df


def read_and_concatenate(input_filepaths):
    """
    Reads CSV files from the given filepaths, using custom headers extracted from each,
    labels them accordingly, and concatenates them into a single DataFrame.

    :param input_filepaths_labels: List of tuples (filepath, label) for the CSV files.
    :return: Concatenated DataFrame.
    """
    dfs = [read_vd(filepath) for filepath in input_filepaths]
    return pd.concat(dfs, ignore_index=True)


def add_missing_columns(df, missing_columns):
    """
    Adds missing columns to the DataFrame with default values set to NaN.

    :param df: The DataFrame to modify.
    :param missing_columns: A list of column names that are missing and need to be added.
    """
    for column in missing_columns:
        if column not in df.columns:
            df[column] = (
                None  # Adding the column with a default value of None (will become NaN in the DataFrame)
            )
    return df




#def update_cg_with_enduses(cg_df, commodity_enduse, process_to_enduses):
#    """
#    Updates cg_df by labeling VAR_FOut rows with end uses and creating corresponding VAR_FIn rows for each end use.
#
#    :param cg_df: DataFrame containing the model's data.
#    :param commodity_enduse: Dictionary mapping commodities to their end uses.
#    :param process_to_enduses: Dictionary mapping processes to lists of end uses.
#    :return: Updated DataFrame.
#    """
#    # Create a copy of the DataFrame to avoid modifying the original DataFrame
#    updated_cg_df = cg_df.copy()
#
#    # Label VAR_FOut rows with their corresponding end uses
#    for idx, row in updated_cg_df[updated_cg_df['Attribute'] == 'VAR_FOut'].iterrows():
#        if row['Commodity'] in commodity_enduse:
#            updated_cg_df.at[idx, 'Enduse'] = commodity_enduse[row['Commodity']]
#
#    # Create new rows for VAR_FIn based on the number of end uses per process
#    new_rows = []
#    for process, enduses in process_to_enduses.items():
#        fin_rows = updated_cg_df[(updated_cg_df['Process'] == process) & (updated_cg_df['Attribute'] == 'VAR_FIn')]
#        for _, fin_row in fin_rows.iterrows():
#            for enduse in enduses:
#                # Copy the existing row and update the Enduse field
#                new_row = fin_row.copy()
#                new_row['Enduse'] = enduse
#                new_rows.append(new_row)
#    # Add the new rows to the DataFrame
#    updated_cg_df = pd.concat([updated_cg_df, pd.DataFrame(new_rows)], ignore_index=True)
#    return updated_cg_df


def df_to_ruleset(df=None, target_column_map=None, parse_column=None, separator=None, schema=None, rule_type=None):
    """
    Reads a DataFrame to create rules for updating or appending to another DataFrame based on
    the contents of a specified column and a mapping of source to target columns. This function
    handles parsing complex descriptions into attributes, mapping values to 'Set' or similar, and
    ensures consistency across complex keys that might map to multiple DataFrame columns.

    An empty string in the schema list is used to indicate parts that should be ignored when creating rules.

    :param df: DataFrame that contains the data to parse.
    :param target_column_map: Dictionary mapping column names in the DataFrame
                              to target DataFrame columns for rule conditions.
    :param parse_column: Column from which to parse data (e.g., 'Description' or 'Set').
    :param separator: Separator used in parse_column to split data into parts.
    :param schema: List of attribute names expected in the parse_column after splitting,
                   use an empty string ("") to ignore parts.
    :param rule_type: Type of rule to create, informing how the rule is applied.
                      E.g., 'inplace' for in-place updates, or 'newrow' for appending new rows.
    :return: A list of rules, each defined as a tuple containing a condition dictionary
             (for matching against DataFrame rows), a rule type (e.g., 'inplace', 'newrow'),
             and a dictionary of attribute updates or values to append.
    """
    assert(df is not None and target_column_map and parse_column and schema and rule_type and separator is not None)
    mapping = {}
    for _, row in df.iterrows():
        # Create the key tuple based on the target_column_map
        key_tuple = tuple(row[col] for col in target_column_map.keys())
        parts = [x.strip() for x in row[parse_column].split(separator)]
        new_mapping = {}
        if len(parts) == len(schema):
            for part, label in zip(parts, schema):
                if label:  # Ignore parts where the schema label is an empty string
                    new_mapping[label] = part
        else:
            logging.warning("Warning: %s for %s does not match expected format. %s: %s",
                            parse_column, key_tuple, parse_column, row[parse_column])
        if new_mapping:
            if key_tuple in mapping and mapping[key_tuple] != new_mapping:
                logging.warning("%s is mapped to different dictionaries. Existing: %s, New: %s",
                                key_tuple, mapping[key_tuple], new_mapping)
            mapping[key_tuple] = new_mapping
    rules = []
    for key_tuple, attributes in mapping.items():
        condition = {target: key for target, key in zip(target_column_map.values(), key_tuple)}
        rules.append((condition, rule_type, attributes))
    return rules

def base_dd_commodity_unit_rules(filepath=None, rule_type=None):
    """
    Extracts the mapping of commodities to units from the specified section of a file.
    Assumes the section starts after 'SET COM_UNIT' and the opening '/', and ends at the next '/'.

    :param base_dd_filepath: Path to the TIMES base.dd file containing the definitions.
    :return: A list of rules, where each rule is a tuple of a condition and actions.
    """
    assert(filepath and rule_type)
    commodity_unit_mapping = {}
    with open(filepath, "r", encoding="utf-8") as file:
        capture = False  # Flag to start capturing data
        for line in file:
            line = line.strip()
            if line.startswith(
                "SET COM_UNIT"
            ):  # Check for start of the relevant section
                capture = True
                continue
            if capture and line.startswith("/"):
                if (
                    not commodity_unit_mapping
                ):  # If the mapping is empty, this is the opening '/'
                    continue
                else:  # If already capturing, this '/' signifies the end
                    break
            if capture and line:
                parts = line.strip("'").split("'.'")
                if len(parts) == 3:
                    region, commodity, unit = parts
                    if unit in SANITIZE_UNITS:
                        unit = SANITIZE_UNITS[unit]
                    commodity_unit_mapping[commodity] = unit
    rules = []
    for commodity, unit in commodity_unit_mapping.items():
        condition = {"Commodity": commodity}
        actions = {"Unit": unit}
        rules.append((condition, rule_type, actions))
    return rules


def sort_rules_by_specificity(rules):
    """
    Sort rules based on their specificity. A rule is considered more specific if its keys
    are a strict superset of the keys of another rule.

    :param rules: A list of tuples, where each tuple contains a condition dictionary and a
                  dictionary of target column(s) and value(s) to set.
    :return: A list of rules sorted from least to most specific.
    """
    # Convert each rule's condition dictionary keys to frozensets for easy comparison
    rule_sets = [
        (frozenset(condition.keys()), condition, rule_type, actions)
        for condition, rule_type, actions in rules
    ]
    # Sort rules based on the length of the condition keys as a primary criterion
    # and the lexicographical order of the keys as a secondary criterion for stability
    sorted_rules = sorted(rule_sets, key=lambda x: (len(x[0]), x[0]))
    # Rebuild sorted rules from sorted rule sets
    sorted_rules_rebuilt = [
        (condition, rule_type, actions) for _, condition, rule_type, actions in sorted_rules
    ]
    return sorted_rules_rebuilt


def apply_rules(schema, rules):
    """
    Apply rules, optimized by minimizing row-wise operations.

    :param schema: DataFrame to apply rules on.
    :param rules: Rules defined as a list of tuples with conditions and actions.
    :return: Modified DataFrame with rules applied.
    """
    sorted_rules = sort_rules_by_specificity(rules)
    new_rows = []
    rows_to_drop = []
    for condition, rule_type, actions in sorted_rules:
        query_conditions_parts, local_vars = [], {}
        for i, (key, value) in enumerate(condition.items()):
            if pd.notna(value) and value != "":
                query_placeholder = f"@value_{i}"
                query_conditions_parts.append(f"`{key}` == {query_placeholder}")
                local_vars[f"value_{i}"] = value
        query_conditions = " & ".join(query_conditions_parts)
        if rule_type == "inplace":
            if not query_conditions:
                continue
            # Filter schema DataFrame based on the query derived from the rule's conditions
            # Pass local_vars to query() to make external variables available
            filtered_indices = schema.query(query_conditions, local_dict=local_vars).index
            # Apply actions for filtered rows, ensuring we ignore empty updates
            for column, value_to_set in actions.items():
                if pd.notna(value_to_set) and value_to_set != "":
                    schema.loc[filtered_indices, column] = value_to_set
        elif rule_type == "newrow":
            # Apply newrow rule logic
            for _, row in schema.iterrows():
                if all(row.get(key, None) == value for key, value in condition.items()):
                    new_row = row.to_dict()
                    new_row.update(actions)
                    new_rows.append(new_row)
        elif rule_type == "drop":
            # Collect indices of rows to drop based on the condition
            if not query_conditions:
                continue
            rows_to_drop.extend(schema.fillna('-').query(query_conditions, local_dict=local_vars).index.tolist())    
    # Drop rows collected for dropping
    schema = schema.drop(rows_to_drop).reset_index(drop=True)
    if new_rows:
        new_rows_df = pd.DataFrame(new_rows)
        schema = pd.concat([schema, new_rows_df], ignore_index=True)
    return schema


def parse_emissions_factors(filename):
    """
    Parses the base.dd file to extract mappings from fuel commodities to emissions commodities.
    
    Args:
    - filename: Path to the base.dd file.
    
    Returns:
    - A dictionary mapping fuel commodities to their corresponding emissions commodities.
    """
    emissions_mapping = {}
    start_parsing = False
    with open(filename, 'r') as file:
        for line in file:
            # Check if the emissions factors section starts.
            if "VDA_EMCB" in line:
                start_parsing = True
                continue
            # If another parameter definition starts, stop parsing.
            if start_parsing and line.startswith("PARAMETER"):
                break
            # Parse the emissions factors lines.
            if start_parsing and line.strip():
                parts = line.split('.')
                if len(parts) >= 4:  # To ensure the line has enough parts to extract data.
                    fuel_commodity = parts[2].strip().replace("'", "")
                    emissions_commodity = parts[3].split()[0].strip().replace("'", "")
                    emissions_mapping[fuel_commodity] = emissions_commodity
    return emissions_mapping


def create_emissions_rules(emissions_dict):
    """
    Creates a set of rules for adding direct emissions rows based solely on input commodities.
    
    :param emissions_dict: Dictionary mapping fuels to their emission categories.
    :return: A list of rules based on the emissions dictionary.
    """
    rules = []
    for input_commodity, emission_commodity in emissions_dict.items():
        rule = ({
            'Attribute': 'VAR_FIn',
            'Commodity': input_commodity  # Trigger on this input commodity
        }, "newrow", {
            'Attribute': 'VAR_FOut',
            'Commodity': emission_commodity,  # Specify the corresponding emission commodity
            'Unit': 'kt CO2',
            'Parameters': 'Emissions'
        })
        rules.append(rule)
    return rules


def stringify_and_strip(df):
    """
    Convert all columns to string and strip whitespace from them.
    """
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
    return df


def compare_rows(df1, df2, df1_label="df1", df2_label="df2"):
    """
    Compare rows of two DataFrames and find rows that are only in one of the two
    DataFrames.

    :param df1: First DataFrame.
    :param df2: Second DataFrame.
    :param df1_label: Label for the first DataFrame.
    :param df2_label: Label for the second DataFrame.
    :return: A DataFrame with all unique rows from both DataFrames and a column
    indicating their source.
    """
    comparison_df = pd.merge(df1, df2, indicator=True, how="outer").query(
        '_merge != "both"'
    )
    return comparison_df


def compare_tables(output_filepath, reference_filepath, columns=None):
    """
    Assemble DataFrames from the output and reference CSV files and compare them.
    Report differences in columns and rows.

    :param output_filepath: Path to the output CSV file.
    :param reference_filepath: Path to the reference CSV file.

    :return: A tuple containing the comparison message, DataFrames, and comparison results.
    """
    output_df = pd.read_csv(output_filepath, low_memory=False).drop_duplicates()
    reference_df = pd.read_csv(reference_filepath, low_memory=False).drop_duplicates()
    if columns is not None:
        output_df = output_df[columns]
        reference_df = reference_df[columns]

    # Convert all columns to string for comparison purposes to ensure compatibility
    output_df = stringify_and_strip(output_df)
    reference_df = stringify_and_strip(reference_df)

    # Compare columns
    missing_columns = set(reference_df.columns) - set(output_df.columns)
    extra_columns = set(output_df.columns) - set(reference_df.columns)

    # Initial message parts
    differences = []
    if missing_columns:
        differences.append(f"Missing columns: {', '.join(missing_columns)}")
    if extra_columns:
        differences.append(f"Extra columns: {', '.join(extra_columns)}")

    # Merge DataFrames to compare rows
    comparison_df = pd.merge(output_df, reference_df, indicator=True, how="outer")

    # Identify correct, missing, and extra rows
    correct_rows = comparison_df[comparison_df["_merge"] == "both"].sort_values(
        by=list(output_df.columns)
    )
    missing_rows = comparison_df[comparison_df["_merge"] == "right_only"].sort_values(
        by=list(output_df.columns)
    )
    extra_rows = comparison_df[comparison_df["_merge"] == "left_only"].sort_values(
        by=list(output_df.columns)
    )

    # Report counts
    differences.append(f"\nNumber of correct rows: {len(correct_rows)}")
    differences.append(f"Number of missing rows: {len(missing_rows)}")
    differences.append(f"Number of extra rows: {len(extra_rows)}")

    with pd.option_context('display.max_rows', None):
        differences.append(f"\nMissing rows:\n {missing_rows.to_string(index=False)}")
        # differences.append(f"\nExtra rows:\n {extra_rows.to_string(index=False)}")

    # Final output
    if differences:
        return (
            "\n".join(differences),
            output_df,
            reference_df,
            correct_rows,
            missing_rows,
            extra_rows,
        )
    return "All good", output_df, reference_df, correct_rows, missing_rows, extra_rows


def compare_rows_to_df(row_extra, row_missing, columns):
    """
    Compares the first rows in extra_rows and missing_rows DataFrames and reports differences
    in a DataFrame format.

    :param row_extra: The first row from extra_rows DataFrame.
    :param row_missing: The first row from missing_rows DataFrame.
    :param columns: List of columns to compare.
    :return: A DataFrame showing differences between the rows.
    """
    # Initialize lists to hold comparison data
    comparison_data = {"Column": [], "Correct Value": [], "Current Value": []}

    # Check if the DataFrames are empty and handle accordingly
    if row_extra.empty or row_missing.empty:
        return pd.DataFrame(
            comparison_data
        )  # Return an empty DataFrame if either row is missing

    for col in columns:
        extra_val = row_extra[col].values[0]
        missing_val = row_missing[col].values[0]
        if extra_val != missing_val:
            comparison_data["Column"].append(col)
            comparison_data["Correct Value"].append(missing_val)
            comparison_data["Current Value"].append(extra_val)

    # Create a DataFrame from the collected comparison data
    comparison_df = pd.DataFrame(comparison_data)
    transposed_df = comparison_df.set_index("Column").T.reset_index()
    return transposed_df


def show_subset(df, column_value_dict):
    """
    Show a subset of the DataFrame where the specified columns match the specified values.

    :param df: The DataFrame to filter.
    :param column_value_dict: A dictionary of column names and values to match.
    :return: The subset of the DataFrame where the specified columns match the specified values.
    """
    query_parts = []
    for column, value in column_value_dict.items():
        query_parts.append(f"{column} == '{value}'")
    query = " & ".join(query_parts)
    return df.query(query)


def save(df, path):
    _df = df.copy()
    _df['Period'] = _df['Period'].astype(int)
    _df['Value'] = _df['Value'].apply(lambda x: f"{x:.6f}")
    _df.to_csv(path, index=False, quoting=csv.QUOTE_ALL)


# Function to find missing periods and create the necessary rows (curried for convenience)
def add_missing_periods(all_periods):
    def _add_missing_periods(group):
        existing_periods = group['Period'].unique()
        missing_periods = np.setdiff1d(all_periods, existing_periods)
        if missing_periods.size > 0:
            # Create new rows for missing periods
            new_rows = pd.DataFrame({
                'Period': missing_periods,
                **{col: group.iloc[0][col] for col in group.columns if col != 'Period'}
            })
            # Set 'Value' to 0 for new rows, assuming 'Value' needs to be filled
            new_rows['Value'] = 0
            return pd.concat([group, new_rows], ignore_index=True)
        return group
    return _add_missing_periods


def process_output_flows(process, scenario, period, df, exclude_co2=True):
     # Return a dictionary mapping commodity to value
     if exclude_co2:
          return df[(df['Process'] == process) &
                    (df['Scenario'] == scenario) &
                    (df['Period'] == period) &
                    (df['Attribute'] == 'VAR_FOut') &
                    ~(df['Commodity'].str.contains('CO2'))].set_index('Commodity')['Value'].to_dict()
     else:
          return df[(df['Process'] == process) &
                    (df['Scenario'] == scenario) &
                    (df['Period'] == period) &
                    (df['Attribute'] == 'VAR_FOut')].set_index('Commodity')['Value'].to_dict()


def process_input_flows(process, scenario, period, df):
     # Return a dictionary mapping commodity to value
     return df[(df['Process'] == process) &
               (df['Scenario'] == scenario) &
               (df['Period'] == period) &
               (df['Attribute'] == 'VAR_FIn')].set_index('Commodity')['Value'].to_dict()


def commodity_output_flows(commodity, scenario, period, df):
     # Return a dictionary of processes and their output values for the given commodity
     return df[(df['Commodity'] == commodity) &
               (df['Scenario'] == scenario) &
               (df['Period'] == period) &
               (df['Attribute'] == 'VAR_FOut') &
               (df['Attribute'] == 'VAR_FOut')].set_index('Process')['Value'].to_dict()


def commodity_input_flows(commodity, scenario, period, df):
     # Return a dictionary of processes the commodity flows into, mapped to flow values
     return df[(df['Commodity'] == commodity) &
               (df['Scenario'] == scenario) &
               (df['Period'] == period) &
               (df['Attribute'] == 'VAR_FIn') &
               (~df['Process'].apply(is_trade_process))].set_index('Process')['Value'].to_dict()



def flow_fractions(flow_dict):
     # Return a dictionary of fractions for each flow
     total = sum(flow_dict.values())
     return {k: v / total for k, v in flow_dict.items()}

def sum_by_key(dicts):
    # Sum values for each key across multiple dictionaries
    result = {}
    for d in dicts:
        for k, v in d.items():
            result[k] = result.get(k, 0) + v
    return result


def process_map_from_commodity_groups(filepath):
    """
    Use the commodity groups file to add rows to the main DataFrame for each process, differentiating between
    energy inputs, energy outputs, CO2 emissions, and end-service energy demands based on the suffix in the Name column.

    :param filepath: Path to the commodity groups file.

    :return: DataFrame with added rows for each process in the commodity groups file.
    """
    cg_df = pd.DataFrame(columns=OUT_COLS + SUP_COLS)
    commodity_groups_df = pd.read_csv(filepath)
    # Define suffixes and their implications
    suffix_mappings = {
        'NRGI': {'Attribute': 'VAR_FIn', 'Parameters': None, 'Unit': None},
        'NRGO': {'Attribute': 'VAR_FOut', 'Parameters': None, 'Unit': None},
        'ENVO': {'Attribute': 'VAR_FOut', 'Parameters': 'Emissions', 'Unit': 'kt CO2'},
        'DEMO': {'Attribute': 'VAR_FOut', 'Parameters': 'End Use Demand', 'Unit': None},
    }
    new_rows = []
    for process in commodity_groups_df['Process'].unique():
        # Always add a VAR_Cap row for each unique process
        new_rows.append({'Attribute': 'VAR_Cap', 'Process': process})
        # Filter rows related to the current process
        process_rows = commodity_groups_df[commodity_groups_df['Process'] == process]
        for _, row in process_rows.iterrows():
            for suffix, attrs in suffix_mappings.items():
                if row['Name'].endswith(suffix):
                    row_data = {
                        'Attribute': attrs['Attribute'],
                        'Process': process,
                        'Commodity': row['Member']
                    }
                    if attrs['Parameters']:
                        row_data['Parameters'] = attrs['Parameters']
                    if attrs['Unit']:
                        row_data['Unit'] = attrs['Unit']
                    new_rows.append(row_data)
    # Convert the list of dictionaries into a DataFrame
    new_rows_df = pd.DataFrame(new_rows)
    # Append the new rows to the main DataFrame and reset the index
    cg_df = pd.concat([cg_df, new_rows_df], ignore_index=True).drop_duplicates()
    return cg_df


def commodities_by_type_from_commodity_groups(filepath):
    """
    Parses the commodity groups file to create mappings from suffix types to sets of associated commodities.

    :param filepath: Path to the commodity groups CSV file.
    :return: Dictionary with suffix types ('NRGI', 'NRGO', 'ENVO', 'DEMO') mapped to sets of commodities.
    """
    commodity_groups_df = pd.read_csv(filepath)
    suffix_mappings = {
        'NRGI': set(),
        'NRGO': set(),
        'ENVO': set(),
        'DEMO': set()
    }
    # Iterate through each row and classify commodities by their suffix in 'Name'
    for _, row in commodity_groups_df.iterrows():
        for suffix in suffix_mappings:
            if row['Name'].endswith(suffix):
                suffix_mappings[suffix].add(row['Member'])
    return suffix_mappings

def matches(pattern):
    return lambda x: bool(pattern.match(x))

is_trade_process = matches(trade_processes)