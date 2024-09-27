"""
Functions used for data processing and transformation, and comparison of DataFrames.
"""

import re
import csv
import logging
import numpy as np
import pandas as pd
from functools import reduce

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


def df_to_ruleset(df=None, target_column_map=None, parse_column=None, separator=None, schema=None, rule_type=None, exclude_filter=None):
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
    if exclude_filter:
        df = df[~exclude_filter(df)]
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


def apply_rules_fast(schema, rules):
    schema = schema.copy()
    conditions_list = []
    all_updates = {}
    sorted_rules = sort_rules_by_specificity(rules)
    for condition, rule_type, updates in sorted_rules:
        condition_df = pd.DataFrame([condition])
        for col, update in updates.items():
            condition_df[col + '_update'] = update
            all_updates[col] = update
        condition_df['rule_type'] = rule_type
        conditions_list.append(condition_df)
    mapping_df = pd.concat(conditions_list, ignore_index=True)
    join_columns = list(set().union(*[condition.keys() for condition, _, _ in rules]))
    schema = schema.merge(mapping_df, on=join_columns, how='left', suffixes=('', '_update'))
    for col in all_updates:
        update_col = col + '_update'
        if update_col in schema.columns:
            is_not_empty = schema[update_col].notna() & (schema[update_col] != '')
            condition = (schema['rule_type'] == 'inplace') & is_not_empty
            schema.loc[condition, col] = schema[update_col]
    schema = schema[schema['rule_type'] != 'drop'].copy()
    schema.drop(columns=[col for col in schema.columns if '_update' in col or col == 'rule_type'], inplace=True)
    return schema


def apply_rules_slow(schema, rules):
    """
    Apply rules, optimized by minimizing row-wise operations.

    :param schema: DataFrame to apply rules on.
    :param rules: Rules defined as a list of tuples with conditions and actions.
    :return: Modified DataFrame with rules applied.
    """
    sorted_rules = sort_rules_by_specificity(rules)
    new_rows = []
    rows_to_drop = []
    for condition, rule_type, updates in sorted_rules:
        if condition:
            query_conditions_parts, local_vars = [], {}
            for i, (key, value) in enumerate(condition.items()):
                if pd.notna(value) and value != "":
                    query_placeholder = f"@value_{i}"
                    query_conditions_parts.append(f"`{key}` == {query_placeholder}")
                    local_vars[f"value_{i}"] = value
            query_conditions = " & ".join(query_conditions_parts)
        else:
            query_conditions = ""
        if rule_type == "inplace":
            if not query_conditions:
                filtered_indices = schema.index
            else:
                # Filter schema DataFrame based on the query derived from the rule's conditions
                # Pass local_vars to query() to make external variables available
                filtered_indices = schema.query(query_conditions, local_dict=local_vars).index
            # Apply updates for filtered rows, ensuring we ignore empty updates
            for column, value_to_set in updates.items():
                if pd.notna(value_to_set) and value_to_set != "":
                    schema.loc[filtered_indices, column] = value_to_set
        elif rule_type == "newrow":
            # Apply newrow rule logic
            for _, row in schema.iterrows():
                if all(row.get(key, None) == value for key, value in condition.items()):
                    new_row = row.to_dict()
                    new_row.update(updates)
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


def appropriate_to_use_apply_rules_fast(rules):
    return bool(rules) and \
        all(rule[1] == 'inplace' for rule in rules) and \
        all(len(rule[0]) > 0 for rule in rules) and \
        all(set(rule[0].keys()) == set(rules[0][0].keys()) for rule in rules) and \
        all(set(rule[2].keys()) == set(rules[0][2].keys()) for rule in rules)


def apply_rules(schema, rules):
    if appropriate_to_use_apply_rules_fast(rules):
        return apply_rules_fast(schema, rules)
    return apply_rules_slow(schema, rules)


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
            'Parameters': 'Emissions', # TODO: should we add a zero Value?
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

def save(df, path):
    _df = df.copy()
    _df['Period'] = _df['Period'].astype(int)
    _df['Value'] = _df['Value'].apply(lambda x: f"{x:.6f}")
    try:
        _df.to_csv(path, index=False, quoting=csv.QUOTE_ALL)
        logging.info(f"Data saved to {path}")
    # If the workbook is open, the file cannot be saved. Warn the user they need to close it.
    except PermissionError:
        logging.warning(f"Permission denied when saving data to {path}. Close it and try again.")
        input("Press Enter to continue...")
        save(df, path)
        return
    except Exception as e:
        logging.error(f"Error saving data to {path}: {e}")
        raise e

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
        'NRGI': {'Attribute': 'VAR_FIn', 'Parameters': '', 'Unit': None},
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

is_elc_exchange_process = matches(elc_exchange_processes)

is_elc_grid_processes = matches(elc_grid_processes)

is_import_process = matches(import_processes)

is_export_process = matches(export_processes)

commodity_map = process_map_from_commodity_groups(ITEMS_LIST_COMMODITY_GROUPS_CSV)

commodities_by_type = commodities_by_type_from_commodity_groups(ITEMS_LIST_COMMODITY_GROUPS_CSV)

end_use_commodities = commodities_by_type['DEMO']

end_use_processes = commodity_map[commodity_map.Commodity.isin(end_use_commodities)].Process.unique()

sector_emission_types = {
    '': 'TOTCO2',
    'Industry': 'INDCO2',
    'Residential' : 'RESCO2',
    'Agriculture' : 'AGRCO2',
    'Electricity' : 'ELCCO2',
    'Transport' : 'TRACO2',
    'Green Hydrogen': 'TOTCO2',
    'Primary Fuel Supply': 'TOTCO2',
    'Commercial': 'COMCO2'
}


def units_consistent(commodity_flow_dict, commodity_units):
     # Check if all units are the same
     return len(set([commodity_units[commodity] for commodity in commodity_flow_dict])) == 1


def trace_commodities(process, scenario, period, df, commodity_units, path=None, fraction=1):
    """
    Trace the output commodities of a process (e.g. Biodiesel blending) all the way through
    to end-use commodities (e.g. bus transportation) to determine what fraction of its output
    (e.g. blended diesel) ends up being used to provide each end-use commodity.
    """
    if path is None:
        path = []
    if len(path) > 100:
        logging.error("Path too long, likely a circular reference")
        logging.error(path)
        raise ValueError("Path too long, likely a circular reference")
    # Extend path with the current process
    current_path = path + [process]
    # Get output flows from the current process
    output_flows = process_output_flows(process, scenario, period, df)
    # This implementation assumes that everything has the same units
    assert(units_consistent(output_flows, commodity_units))
    # Calculate fractional flows for each output commodity
    output_fracs = flow_fractions(output_flows)
    # Resulting dictionary to keep track of the final fractional attributions
    result = {}
    for commodity in output_flows.keys():
        # Get the input flows for the commodity across different processes
        input_flows = commodity_input_flows(commodity, scenario, period, df)
        # If the commodity does not flow into any other processes, it is terminal
        if not input_flows:
            # Save the path and fraction up to this point
            result[tuple(current_path + [commodity])] = fraction * output_fracs[commodity]
        else:
            input_fracs = flow_fractions(input_flows)
            # Recursively trace downstream processes
            for downstream_process, input_fraction in input_fracs.items():
                ####    continue
                # Calculate new fraction as current fraction * fraction of this commodity's output used by the downstream process
                new_fraction = fraction * output_fracs[commodity] * input_fraction
                # Merge results from recursion
                result.update(trace_commodities(downstream_process, scenario, period, df, commodity_units, current_path + [commodity], new_fraction))
    return result


def end_use_fractions(process, scenario, period, df, commodity_units, filter_to_commodities=None):
    # Return a dictionary of emissions from end-use processes
    trace_result = trace_commodities(process, scenario, period, df, commodity_units)
    # Ensure the sum of all terminal fractions is approximately 1
    assert(abs(sum(trace_result.values()) - 1) < 1e-5)
    end_use_fractions = pd.DataFrame(
         [{'Scenario': scenario,
         'Attribute': 'VAR_FOut',
         'Commodity': None,
         'Process': process,
         'Period': period,
         'Value': None} for process in end_use_processes]
    )
    # Loop through the trace_result dictionary
    for key, value in trace_result.items():
        process_chain = key  # This is the tuple containing the process chain
        fuel_source_process = process_chain[0] # First entry which is the fuel source process
        process = process_chain[-2]  # Penultimate entry which is the process
        commodity = process_chain[1]  # Second entry which is the commodity
        end_use_fractions.loc[end_use_fractions['Process'] == process, 'Value'] = value
        end_use_fractions.loc[end_use_fractions['Process'] == process, 'Commodity'] = commodity
        end_use_fractions.loc[end_use_fractions['Process'] == process, 'FuelSourceProcess'] = fuel_source_process
    if filter_to_commodities is not None:
        end_use_fractions = end_use_fractions[(end_use_fractions['Commodity'].isin(filter_to_commodities)) | (end_use_fractions['Commodity'].isna())]
    end_use_fractions.Value = end_use_fractions.Value / end_use_fractions.Value.sum()
    return end_use_fractions


def fix_multiple_fout(df):
    filtered_df = df[(df['Attribute'] == 'VAR_FOut') & (~df['Commodity'].str.contains('CO2'))]
    multi_fout = filtered_df.groupby(['Scenario', 'Process', 'Period']).filter(lambda x: len(x) > 1)
    unique_scenario_process_periods = multi_fout[['Scenario', 'Process', 'Period']].drop_duplicates()
    for _, row in unique_scenario_process_periods.iterrows():
        scen = row['Scenario']
        process = row['Process']
        period = row['Period']
        logging.info(f"Processing Scenario: {scen}, Process: {process}, Period: {period}")
        # Filter relevant rows for the current process and period
        relevant_rows = df[(df['Scenario'] == scen) & (df['Process'] == process) & (df['Period'] == period)]
        fin_row = relevant_rows[relevant_rows['Attribute'] == 'VAR_FIn']
        assert(len(fin_row) == 1)  # There should only be one VAR_FIn row - currently not handling multiple VAR_FIn rows
        fout_rows = relevant_rows[relevant_rows['Attribute'] == 'VAR_FOut']
        if not fin_row.empty:
            total_output = fout_rows['Value'].sum()
            ratios = fout_rows['Value'] / total_output
            # Create new VAR_FIn rows by multiplying the original Value with each ratio
            new_fin_rows = fin_row.copy().loc[fin_row.index.repeat(len(fout_rows))].reset_index(drop=True)
            new_fin_rows['Value'] = fin_row['Value'].values[0] * ratios.values
            new_fin_rows['Enduse'] = fout_rows['Enduse'].values
            # Replace the original VAR_FIn row with the new rows in the DataFrame
            df = df.drop(fin_row.index)  # Remove original VAR_FIn row
            df = pd.concat([df, new_fin_rows], ignore_index=True)
    return df


def apply_rulesets(df, rulesets, subset_name=None):
    # Complete the dataframe using the usual rules, taking care not to overwrite the Fuel
    for name, ruleset in rulesets:
        logging.info(f"Applying ruleset to '{subset_name}' rows: %s", name)
        df = apply_rules(df, ruleset)
    return df


def allocate_to_enduse_processes(rows_to_reallocate, main_df, commodity_units, filter_to_commodities=None):
    rows_to_add = pd.DataFrame()
    for _, row in rows_to_reallocate.iterrows():
        # For each negative emission process, follow its outputs through to end uses;
        # get the fractional attributions of the process output to end-use processes
        if filter_to_commodities is not None:
            end_use_allocations = end_use_fractions(row['Process'], row['Scenario'], row['Period'], main_df, commodity_units, filter_to_commodities=filter_to_commodities)
        else:
            end_use_allocations = end_use_fractions(row['Process'], row['Scenario'], row['Period'], main_df, commodity_units)
        # Proportionately attribute the 'neg-emissions' to the end-uses, in units of Mt CO₂/yr
        end_use_allocations['Value'] *= row['Value']
        # Tidy up and add the new rows to emissions_rows_to_add
        end_use_allocations = end_use_allocations[~end_use_allocations['Value'].isna()]
        #end_use_allocations = add_missing_columns(end_use_allocations, OUT_COLS)
        rows_to_add = pd.concat([rows_to_add, end_use_allocations], ignore_index=True)
    return rows_to_add


def fixup_emissions_attributed_to_emitting_fuels(df):
    processes_to_fix = df[(df['Fuel'].isin(NON_EMISSION_FUEL)) & (df['Parameters'] == 'Emissions')].Process.unique()
    for process in processes_to_fix:
        process_clean_fuel = df.loc[
            (df['Fuel'].isin(NON_EMISSION_FUEL)) &
            (df['Parameters'] == 'Emissions') &
            (df['Process'] == process), 'Fuel'].unique()[0]
        process_all_fuels = df.loc[df['Process'] == process, 'Fuel'].unique()
        assert any(fuel not in NON_EMISSION_FUEL for fuel in process_all_fuels), "No emitting fuel found in the process."
        process_emitting_fuel = next((fuel for fuel in process_all_fuels if fuel not in NON_EMISSION_FUEL), None)
        indices_to_update = (df['Fuel'] == process_clean_fuel) & \
                            (df['Parameters'] == 'Emissions') & \
                            (df['Process'] == process)
        df.loc[indices_to_update, 'Fuel'] = process_emitting_fuel
        df.loc[indices_to_update, 'FuelGroup'] = 'Fossil Fuels'
    return df


def complete_expand_dim(df, expand_dim, fill_value_dict):
    original_column_order = df.columns
    # This implementation assumes no NaN values in the starting DataFrame
    assert not df.isnull().values.any(), "DataFrame contains NaN values"
    # Get all columns except the one to expand
    defcols = [expand_dim] + list(fill_value_dict.keys()) # defined columns
    columns = [x for x in df.columns if x not in defcols] # derived from data
    # Form a DataFrame with all combinations of the unique values of the other dimensions
    _df = df.copy().drop(columns=defcols).drop_duplicates()
    _df['key'] = 1
    # Get all unique values for the expansion dimension
    # Create a DataFrame with all expand_dim values and the same key
    expand_values = df[expand_dim].unique()
    expand_df = pd.DataFrame({expand_dim: expand_values, 'key': 1})
    # Combine the unique values of the expand_dim with the original DataFrame using the key
    # This creates a DataFrame where each row of the original is repeated for each unique value of the expand_dim
    df_expanded = pd.merge(_df, expand_df, on='key').drop(columns='key')
    # Merge the expanded DataFrame with the original DataFrame to fill in the missing values
    df_full = pd.merge(df_expanded, df, on=columns + [expand_dim], how='left')
    # for each column in fill_value_dict, fill in the missing values with the specified default
    for (col, fill_value) in fill_value_dict.items():
        df_full[col] = df_full[col].fillna(fill_value)
    return df_full[original_column_order]


def sanity_check(subset, full_df, match_columns, tolerance, factor=1, name=""):
    grouped_subset_values = subset.groupby(['Scenario', 'Period']).Value.sum()
    for (scenario, period), value in grouped_subset_values.items():
        conditions = [
            (full_df.Scenario == scenario),
            (full_df.Period == period)
        ]
        for col, values in match_columns.items():
            if isinstance(values, list):
                condition = full_df[col].isin(values)
            else:
                condition = (full_df[col] == values)
            conditions.append(condition)
        final_condition = reduce(np.logical_and, conditions)
        rows_in_dataframe = full_df[final_condition]
        assert abs(rows_in_dataframe.Value.sum() * factor - value) < tolerance, "Value does not match within tolerance"
        logging.info(f"Check {name} output matches for Scenario: {scenario}, Period: {period}, Summed Value: {value:.2f}: OK")


def check_enduse_rows(df):
    enduse_df = df.loc[(df.ProcessSet == '.DMD.') | (df.CommoditySet == '.DEM.')]
    nan_tech = enduse_df.loc[enduse_df.Technology.isna()]
    nan_enduse = enduse_df.loc[enduse_df.Enduse.isna()]
    nan_fuel = enduse_df.loc[enduse_df.Fuel.isna()]
    nan_fuelgroup = enduse_df.loc[enduse_df.FuelGroup.isna()]
    nan_technology_group = enduse_df.loc[enduse_df.Technology_Group.isna()]
    nan_process_set = enduse_df.loc[enduse_df.ProcessSet.isna()]
    nan_commodity_set = enduse_df.loc[enduse_df.CommoditySet.isna()]
    nan_value = enduse_df.loc[enduse_df.Value.isna()]
    assert nan_tech.empty, f"Missing Technology: {nan_tech}"
    assert nan_enduse.empty, f"Missing Enduse: {nan_enduse}"
    assert nan_fuel.empty, f"Missing Fuel {nan_fuel}"
    assert nan_fuelgroup.empty, f"Missing FuelGroup {nan_fuelgroup}"
    assert nan_technology_group.empty, f"Missing Technology_Group {nan_technology_group}"
    assert nan_process_set.empty, f"Missing ProcessSet {nan_process_set}"
    assert nan_commodity_set.empty, f"Missing CommoditySet {nan_commodity_set}"
    assert nan_value.empty, f"Missing Value {nan_value}"


def check_missing_tech(df, schema_technology):
    enduse_df = df.loc[(df.ProcessSet == '.DMD.') | (df.CommoditySet == '.DEM.')]
    elegen_df = df.loc[(df.Sector == 'Electricity') & (df.ProcessSet == '.ELE.')]
    elefue_df = df.loc[(df.Sector == 'Other') & (df.Parameters == 'Fuel Consumption')]
    missing_tech = enduse_df.loc[~enduse_df.Technology.isin(schema_technology['Technology'])]
    if not missing_tech.empty:
        raise ValueError(f"Missing Technologies found: {missing_tech.Technology.unique()}")
    missing_tech = elegen_df.loc[~elegen_df.Technology.isin(schema_technology['Technology'])]
    if not missing_tech.empty:
        raise ValueError(f"Missing Technologies found: {missing_tech.Technology.unique()}")
    missing_tech = elefue_df.loc[~elefue_df.Technology.isin(schema_technology['Technology'])]
    if not missing_tech.empty:
        raise ValueError(f"Missing Technologies found: {missing_tech.Technology.unique()}")


def check_electricity_fuel_consumption(df):
    electricity_rows = df[(df['Sector'] == 'Other')]
    electricity_fuel_consumption = electricity_rows[(electricity_rows['Parameters'] == 'Fuel Consumption')]
    assert electricity_fuel_consumption.loc[electricity_fuel_consumption.Attribute=='VAR_FIn'].ProcessSet.unique().tolist() == ['.ELE.'], "Electricity fuel consumption not just from Electricity generation processes"


def negated_rows(df, rules):
    neg_df = df.copy()
    neg_df['Value'] = -neg_df['Value']
    neg_df = apply_rules(neg_df, rules)
    return neg_df


def spread_to_all_aviation(drop_in_jet_domestic_rows_to_add, main_df):
    # Inherited from earlier data processing - create a copy to share DIJ consumption between domestic and international jet travel
    # Split the drop-in-jet between domestic and international jet travel pro-rata by scenario and period.
    # A better approach might be to implement this within TIMES instead of post-processing.
    drop_in_jet_international_rows_to_add = drop_in_jet_domestic_rows_to_add.copy()
    drop_in_jet_international_rows_to_add['Value'] = 0
    drop_in_jet_international_rows_to_add['Enduse'] = 'International Aviation'
    drop_in_jet_international_rows_to_add['Process'] = 'T_O_FuelJet_Int'
    for index, row in drop_in_jet_domestic_rows_to_add.iterrows():
        domestic_jet_travel = process_output_flows('T_O_FuelJet', row['Scenario'], row['Period'], main_df)['T_O_JET']
        internat_jet_travel = process_output_flows('T_O_FuelJet_Int', row['Scenario'], row['Period'], main_df)['T_O_JET_Int']
        domestic_jet_value = row['Value'] * domestic_jet_travel / (internat_jet_travel + domestic_jet_travel)
        internat_jet_value = row['Value'] * internat_jet_travel / (internat_jet_travel + domestic_jet_travel)
        drop_in_jet_domestic_rows_to_add.loc[index, 'Value'] = domestic_jet_value
        drop_in_jet_international_rows_to_add.loc[index, 'Value'] = internat_jet_value
    drop_in_jet_rows_to_add = pd.concat([drop_in_jet_domestic_rows_to_add, drop_in_jet_international_rows_to_add], ignore_index=True)
    return drop_in_jet_rows_to_add
