"""
Functions used for data processing and transformation.
"""

import os
import re
import csv
import logging
from functools import reduce
import numpy as np
import pandas as pd

import constants

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# pylint: disable=too-many-lines, too-many-branches, too-many-arguments

def read_vd(filepath):
    """
    Reads a VD file, using column names extracted from the file's
    header with regex, skipping non-CSV formatted header lines.

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
    vd_df = pd.read_csv(
        filepath, skiprows=skiprows, names=columns, header=None, low_memory=False
    )
    return vd_df


def load_and_concatenate(scenario_input_files):
    """
    Load and concatenate the VEDA data files for the given scenarios.

    Parameters
    ----------
    scenario_input_files : dict
        A dictionary with scenario names as keys and file paths as values.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the concatenated data from all scenarios.
    """
    raw_df = pd.DataFrame()
    exclude_periods = ["2020"]
    # Read the VEDA Data (VD) files
    for scen, path in scenario_input_files.items():
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        scen_df = read_vd(path)
        scen_df = scen_df[~scen_df["Period"].isin(exclude_periods)]
        scen_df["Scenario"] = scen
        raw_df = pd.concat([raw_df, scen_df])
    return raw_df


# pylint: disable=too-many-arguments, too-many-locals
def df_to_ruleset(
    dataframe=None,
    target_column_map=None,
    parse_column=None,
    separator=None,
    schema=None,
    rule_type=None,
    exclude_filter=None,
):
    """
    Reads a DataFrame to create rules for updating
    or appending to another DataFrame based on
    the contents of a specified column and a mapping
    of source to target columns. This function
    handles parsing complex descriptions into attributes,
    mapping values to 'Set' or similar, and ensures
    consistency across complex keys that might map to
    multiple DataFrame columns.

    An empty string in the schema list is used to indicate
    parts that should be ignored when creating rules.

    :param dataframe:
        DataFrame that contains the data to parse.
    :param target_column_map:
        Dictionary mapping column names in the DataFrame
        to target DataFrame columns for rule conditions.
    :param parse_column:
        Column from which to parse data (e.g., 'Description' or 'Set').
    :param separator:
        Separator used in parse_column to split data into parts.
    :param schema:
        List of attribute names expected in the parse_column after splitting,
        use an empty string ("") to ignore parts.
    :param rule_type:
        Type of rule to create, informing how the rule is applied.
        E.g., 'inplace' for in-place updates, or 'newrow' for appending new rows.
    :return:
        A list of rules, each defined as a tuple containing a condition dictionary
        (for matching against DataFrame rows), a rule type (e.g., 'inplace', 'newrow'),
        and a dictionary of attribute updates or values to append.
    """
    assert (
        dataframe is not None
        and target_column_map
        and parse_column
        and schema
        and rule_type
        and separator is not None
    )
    if exclude_filter:
        dataframe = dataframe[~exclude_filter(dataframe)]
    mapping = {}
    for _, row in dataframe.iterrows():
        key_tuple = tuple(row[col] for col in target_column_map.keys())
        parts = [x.strip() for x in row[parse_column].split(separator)]
        new_mapping = {}
        if len(parts) == len(schema):
            for part, label in zip(parts, schema):
                if label:
                    new_mapping[label] = part
        else:
            logging.warning(
                "Warning: %s for %s does not match expected format. %s: %s",
                parse_column,
                key_tuple,
                parse_column,
                row[parse_column],
            )
        if new_mapping:
            if key_tuple in mapping and mapping[key_tuple] != new_mapping:
                logging.warning(
                    "%s is mapped to different dictionaries. Existing: %s, New: %s",
                    key_tuple,
                    mapping[key_tuple],
                    new_mapping,
                )
            mapping[key_tuple] = new_mapping
    rules = []
    for key_tuple, attributes in mapping.items():
        condition = dict(zip(target_column_map.values(), key_tuple))
        rules.append((condition, rule_type, attributes))
    return rules


def base_dd_commodity_unit_rules(filepath=None, rule_type=None):
    """
    Extracts the mapping of commodities to units from the specified section of a file.
    Assumes the section starts after 'SET COM_UNIT' and the opening '/', and ends at the next '/'.

    :param base_dd_filepath: Path to the TIMES base.dd file containing the definitions.
    :return: A list of rules, where each rule is a tuple of a condition and actions.
    """
    assert filepath and rule_type
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
                break
            if capture and line:
                parts = line.strip("'").split("'.'")
                if len(parts) == 3:
                    _, commodity, unit = parts
                    if unit in constants.SANITIZE_UNITS:
                        unit = constants.SANITIZE_UNITS[unit]
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
        (condition, rule_type, actions)
        for _, condition, rule_type, actions in sorted_rules
    ]
    return sorted_rules_rebuilt


def apply_rules_fast(schema, rules):
    """
    Apply rules to the schema DataFrame using a join operation.

    :param schema: DataFrame to apply rules on.
    :param rules: Rules defined as a list of tuples with conditions and actions.
    :return: Modified DataFrame with rules applied.

    This function is optimized for performance by minimizing row-wise operations.
    It is only appropriate for rules that can be expressed as a join operation.
    """
    schema = schema.copy()
    conditions_list = []
    all_updates = {}
    sorted_rules = sort_rules_by_specificity(rules)
    for condition, rule_type, updates in sorted_rules:
        condition_df = pd.DataFrame([condition])
        for col, update in updates.items():
            condition_df[col + "_update"] = update
            all_updates[col] = update
        condition_df["rule_type"] = rule_type
        conditions_list.append(condition_df)
    mapping_df = pd.concat(conditions_list, ignore_index=True)
    join_columns = list(set().union(*[condition.keys() for condition, _, _ in rules]))
    schema = schema.merge(
        mapping_df, on=join_columns, how="left", suffixes=("", "_update")
    )
    for col in all_updates:
        update_col = col + "_update"
        if update_col in schema.columns:
            is_not_empty = schema[update_col].notna() & (schema[update_col] != "")
            condition = (schema["rule_type"] == "inplace") & is_not_empty
            schema.loc[condition, col] = schema[update_col]
    schema = schema[schema["rule_type"] != "drop"].copy()
    schema.drop(
        columns=[
            col for col in schema.columns if "_update" in col or col == "rule_type"
        ],
        inplace=True,
    )
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
                # Filter schema DataFrame based on the
                # query derived from the rule's conditions
                # Pass local_vars to query() to make
                # external variables available
                filtered_indices = schema.query(
                    query_conditions, local_dict=local_vars
                ).index
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
            rows_to_drop.extend(
                schema.fillna("-")
                .query(query_conditions, local_dict=local_vars)
                .index.tolist()
            )
    # Drop rows collected for dropping
    schema = schema.drop(rows_to_drop).reset_index(drop=True)
    if new_rows:
        new_rows_df = pd.DataFrame(new_rows)
        schema = pd.concat([schema, new_rows_df], ignore_index=True)
    return schema


def appropriate_to_use_apply_rules_fast(rules):
    """
    Check if it is appropriate to use the fast version of apply_rules.

    This is the case if the rules are equivalent to a dataframe join operation.

    :param rules: A list of rules to check.
    :return: True if the rules are appropriate for the fast version, False otherwise.
    """
    return (
        bool(rules)
        and all(rule[1] == "inplace" for rule in rules)
        and all(len(rule[0]) > 0 for rule in rules)
        and all(set(rule[0].keys()) == set(rules[0][0].keys()) for rule in rules)
        and all(set(rule[2].keys()) == set(rules[0][2].keys()) for rule in rules)
    )


def apply_rules(schema, rules):
    """
    Apply rules to the schema DataFrame.
    Uses apply_rules_fast where appropriate.

    :param schema:
        DataFrame to apply rules on.
    :param rules:
        Rules defined as a list of tuples with conditions and actions.

    :return: Modified DataFrame with rules applied.
    """
    if appropriate_to_use_apply_rules_fast(rules):
        return apply_rules_fast(schema, rules)
    return apply_rules_slow(schema, rules)


def parse_emissions_factors(filename):
    """
    Parses the base.dd file to extract mappings
    from fuel commodities to emissions commodities.

    Args:
    - filename:
        Path to the base.dd file.

    Returns:
    - A dictionary mapping fuel commodities
        to their corresponding emissions commodities.
    """
    emissions_mapping = {}
    start_parsing = False
    with open(filename, "r", encoding="utf-8") as file:
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
                parts = line.split(".")
                if (
                    len(parts) >= 4
                ):  # To ensure the line has enough parts to extract data.
                    fuel_commodity = parts[2].strip().replace("'", "")
                    emissions_commodity = parts[3].split()[0].strip().replace("'", "")
                    emissions_mapping[fuel_commodity] = emissions_commodity
    return emissions_mapping


def create_emissions_rules(emissions_dict):
    """
    Creates a set of rules for adding direct
    emissions rows based solely on input commodities.

    :param emissions_dict:
        Dictionary mapping fuels to their emission categories.
    :return:
        A list of rules based on the emissions dictionary.
    """
    rules = []
    for input_commodity, emission_commodity in emissions_dict.items():
        rule = (
            {
                "Attribute": "VAR_FIn",
                "Commodity": input_commodity,
            },
            "newrow",
            {
                "Attribute": "VAR_FOut",
                "Commodity": emission_commodity,
                "Unit": "kt CO2",
                "Parameters": "Emissions",
            },
        )
        rules.append(rule)
    return rules


#def stringify_and_strip(dataframe):
#    """
#    Convert all columns to string and strip whitespace from them.
#    """
#    for col in dataframe.columns:
#        dataframe[col] = dataframe[col].astype(str).str.strip()
#    return dataframe


def save(dataframe, path):
    """
    Save the DataFrame to a CSV file. If the file
    is open, prompt the user to close it and try again.

    :param df: DataFrame to save.
    :param path: Path to save the DataFrame to.

    """
    _dataframe = dataframe.copy()
    _dataframe["Period"] = _dataframe["Period"].astype(int)
    _dataframe["Value"] = _dataframe["Value"].apply(lambda x: f"{x:.6f}")
    try:
        _dataframe.to_csv(path, index=False, quoting=csv.QUOTE_ALL)
        logging.info("Data saved to %s", path)
    except PermissionError:
        logging.warning(
            "Permission denied when saving data to %s. Close it and try again.",
            path
        )
        input("Press Enter to continue...")
        save(dataframe, path)
        return
    except Exception as error:
        logging.error("Error saving data to %s: %s", path, error)
        raise error


# Function to find missing periods and create the
# necessary rows (curried for convenience)
def add_missing_periods(all_periods):
    """
    Curried function used to add missing periods to
    a dataframe and fill the 'Value' column with 0.

    :param all_periods: List of all periods to ensure present.
    :return: A function that adds missing periods to a dataframe.

    Usage example:

    clean_df = clean_df.groupby(categories).apply(
        add_missing_periods(all_periods)
    ).reset_index(drop=True)

    """

    def _add_missing_periods(group):
        existing_periods = group["Period"].unique()
        missing_periods = np.setdiff1d(all_periods, existing_periods)
        if missing_periods.size > 0:
            # Create new rows for missing periods
            new_rows = pd.DataFrame(
                {
                    "Period": missing_periods,
                    **{
                        col: group.iloc[0][col]
                        for col in group.columns
                        if col != "Period"
                    },
                }
            )
            # Set 'Value' to 0 for new rows, assuming 'Value' needs to be filled
            new_rows["Value"] = 0
            return pd.concat([group, new_rows], ignore_index=True)
        return group

    return _add_missing_periods


def process_output_flows(process, scenario, period, dataframe, exclude_co2=True):
    """
    Return a dictionary mapping commodity to value

       :param process: The process to filter by.
       :param scenario: The scenario to filter by.
       :param period: The period to filter by.
       :param dataframe: The DataFrame to filter.

       :return: A dictionary mapping commodity to output flow.
    """
    if exclude_co2:
        return (
            dataframe[
                (dataframe["Process"] == process)
                & (dataframe["Scenario"] == scenario)
                & (dataframe["Period"] == period)
                & (dataframe["Attribute"] == "VAR_FOut")
                & ~(dataframe["Commodity"].str.contains("CO2"))
            ]
            .set_index("Commodity")["Value"]
            .to_dict()
        )
    return (
        dataframe[
            (dataframe["Process"] == process)
            & (dataframe["Scenario"] == scenario)
            & (dataframe["Period"] == period)
            & (dataframe["Attribute"] == "VAR_FOut")
        ]
        .set_index("Commodity")["Value"]
        .to_dict()
    )


def process_input_flows(process, scenario, period, dataframe):
    """
    Return a dictionary mapping commodity to value

    :param process: The process to filter by.
    :param scenario: The scenario to filter by.
    :param period: The period to filter by.
    :param dataframe: The DataFrame to filter.

    :return: A dictionary mapping commodity to input flow.
    """
    return (
        dataframe[
            (dataframe["Process"] == process)
            & (dataframe["Scenario"] == scenario)
            & (dataframe["Period"] == period)
            & (dataframe["Attribute"] == "VAR_FIn")
        ]
        .set_index("Commodity")["Value"]
        .to_dict()
    )


def commodity_output_flows(commodity, scenario, period, dataframe):
    """
    Return a dictionary of processes and their output
    values for the given commodity

    :param commodity: The commodity to filter by.
    :param scenario: The scenario to filter by.
    :param period: The period to filter by.
    :param dataframe: The DataFrame to filter.

    :return: A dictionary of processes and their output
    values for the given commodity.
    """
    return (
        dataframe[
            (dataframe["Commodity"] == commodity)
            & (dataframe["Scenario"] == scenario)
            & (dataframe["Period"] == period)
            & (dataframe["Attribute"] == "VAR_FOut")
            & (dataframe["Attribute"] == "VAR_FOut")
        ]
        .set_index("Process")["Value"]
        .to_dict()
    )


def commodity_input_flows(commodity, scenario, period, dataframe):
    """
    Return a dictionary of processes the commodity
    flows into, mapped to flow values

    :param commodity: The commodity to filter by.
    :param scenario: The scenario to filter by.
    :param period: The period to filter by.
    :param df: The DataFrame to filter.

    :return: A dictionary mapping processes to input flow.
    """
    return (
        dataframe[
            (dataframe["Commodity"] == commodity)
            & (dataframe["Scenario"] == scenario)
            & (dataframe["Period"] == period)
            & (dataframe["Attribute"] == "VAR_FIn")
            & (~dataframe["Process"].apply(is_trade_process))
        ]
        .set_index("Process")["Value"]
        .to_dict()
    )


def flow_fractions(flow_dict):
    """
    Return a dictionary of fractions for each flow

    :param flow_dict: Dictionary of flows to calculate fractions for.

    :return: A dictionary of fractions for each flow.
    """
    total = sum(flow_dict.values())
    return {key: val / total for key, val in flow_dict.items()}


def sum_by_key(dicts):
    """
    Sum values for each key across multiple dictionaries

    :param dicts: List of dictionaries to sum values for each key.

    :return: A dictionary with summed values for each key.
    """
    result = {}
    for this_dict in dicts:
        for key, val in this_dict.items():
            result[key] = result.get(key, 0) + val
    return result


def process_map_from_commodity_groups(filepath):
    """
    Use the commodity groups file to add rows to the main
    DataFrame for each process, differentiating between
    energy inputs, energy outputs, CO2 emissions, and
    end-service energy demands based on the suffix in the
    Name column.

    :param filepath: Path to the commodity groups file.

    :return: DataFrame with added rows for each process
        in the commodity groups file.
    """
    cg_df = pd.DataFrame(columns=constants.OUT_COLS + constants.SUP_COLS)
    commodity_groups_df = pd.read_csv(filepath)
    # Define suffixes and their implications
    suffix_mappings = {
        "NRGI": {"Attribute": "VAR_FIn", "Parameters": "", "Unit": None},
        "NRGO": {"Attribute": "VAR_FOut", "Parameters": None, "Unit": None},
        "ENVO": {"Attribute": "VAR_FOut", "Parameters": "Emissions", "Unit": "kt CO2"},
        "DEMO": {"Attribute": "VAR_FOut", "Parameters": "End Use Demand", "Unit": None},
    }
    new_rows = []
    for process in commodity_groups_df["Process"].unique():
        # Always add a VAR_Cap row for each unique process
        new_rows.append({"Attribute": "VAR_Cap", "Process": process})
        # Filter rows related to the current process
        process_rows = commodity_groups_df[commodity_groups_df["Process"] == process]
        for _, row in process_rows.iterrows():
            for suffix, attrs in suffix_mappings.items():
                if row["Name"].endswith(suffix):
                    row_data = {
                        "Attribute": attrs["Attribute"],
                        "Process": process,
                        "Commodity": row["Member"],
                    }
                    if attrs["Parameters"]:
                        row_data["Parameters"] = attrs["Parameters"]
                    if attrs["Unit"]:
                        row_data["Unit"] = attrs["Unit"]
                    new_rows.append(row_data)
    # Convert the list of dictionaries into a DataFrame
    new_rows_df = pd.DataFrame(new_rows)
    # Append the new rows to the main DataFrame and reset the index
    cg_df = pd.concat([cg_df, new_rows_df], ignore_index=True).drop_duplicates()
    return cg_df


def commodities_by_type_from_commodity_groups(filepath):
    """
    Parses the commodity groups file to create mappings
    from suffix types to sets of associated commodities.

    :param filepath:
        Path to the commodity groups CSV file.
    :return:
        Dictionary with suffix types ('NRGI', 'NRGO',
        'ENVO', 'DEMO') mapped to sets of commodities.
    """
    commodity_groups_df = pd.read_csv(filepath)
    suffix_mappings = {"NRGI": set(), "NRGO": set(), "ENVO": set(), "DEMO": set()}
    # Iterate through each row and classify commodities by their suffix in 'Name'
    for _, row in commodity_groups_df.iterrows():
        for suffix, mapping in suffix_mappings.items():
            if row["Name"].endswith(suffix):
                mapping.add(row["Member"])
    return suffix_mappings


def matches(pattern):
    """
    Use a compiled regex pattern to create a lambda function

    :param pattern: Compiled regex pattern to match against.
    :return: Lambda function that returns True if the pattern matches.
    """
    return lambda x: bool(pattern.match(x))


is_trade_process = matches(constants.trade_processes)

is_elc_exchange_process = matches(constants.elc_exchange_processes)

is_elc_grid_processes = matches(constants.elc_grid_processes)

is_import_process = matches(constants.import_processes)

is_export_process = matches(constants.export_processes)

commodity_map = process_map_from_commodity_groups(constants.ITEMS_LIST_COMMODITY_GROUPS_CSV)

commodities_by_type = commodities_by_type_from_commodity_groups(
    constants.ITEMS_LIST_COMMODITY_GROUPS_CSV
)

end_use_commodities = commodities_by_type["DEMO"]

end_use_processes = commodity_map[
    commodity_map.Commodity.isin(end_use_commodities)
].Process.unique()

sector_emission_types = {
    "": "TOTCO2",
    "Industry": "INDCO2",
    "Residential": "RESCO2",
    "Agriculture": "AGRCO2",
    "Electricity": "ELCCO2",
    "Transport": "TRACO2",
    "Green Hydrogen": "TOTCO2",
    "Primary Fuel Supply": "TOTCO2",
    "Commercial": "COMCO2",
}


def units_consistent(commodity_flow_dict, commodity_units):
    """
    Check if all units are the same

    :param commodity_flow_dict: Dictionary of commodity flows.
    :param commodity_units: Dictionary of commodity units.

    :return: True if all units are the same, False otherwise.
    """
    return (
        len({commodity_units[commodity] for commodity in commodity_flow_dict}) == 1
    )


def trace_commodities(
    process, scenario, period, dataframe, commodity_units, path=None, fraction=1
):
    """
    Trace the output commodities of a process
    (e.g. Biodiesel blending) all the way through
    to end-use commodities (e.g. bus transportation)
    to determine what fraction of its output
    (e.g. blended diesel) ends up being used to
    provide each end-use commodity.
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
    output_flows = process_output_flows(process, scenario, period, dataframe)
    # This implementation assumes that everything has the same units
    assert units_consistent(output_flows, commodity_units)
    # Calculate fractional flows for each output commodity
    output_fracs = flow_fractions(output_flows)
    # Resulting dictionary to keep track of the final fractional attributions
    result = {}
    for commodity in output_flows.keys():
        # Get the input flows for the commodity across different processes
        input_flows = commodity_input_flows(commodity, scenario, period, dataframe)
        # If the commodity does not flow into any other processes, it is terminal
        if not input_flows:
            # Save the path and fraction up to this point
            result[tuple(current_path + [commodity])] = (
                fraction * output_fracs[commodity]
            )
        else:
            input_fracs = flow_fractions(input_flows)
            # Recursively trace downstream processes
            for downstream_process, input_fraction in input_fracs.items():
                ####    continue
                # Calculate new fraction as current fraction * fraction
                # of this commodity's output used by the downstream process
                new_fraction = fraction * output_fracs[commodity] * input_fraction
                # Merge results from recursion
                result.update(
                    trace_commodities(
                        downstream_process,
                        scenario,
                        period,
                        dataframe,
                        commodity_units,
                        current_path + [commodity],
                        new_fraction,
                    )
                )
    return result


def end_use_fractions(
    process, scenario, period, dataframe, commodity_units, filter_to_commodities=None
):
    """
    Return a dictionary of emissions from end-use processes

    :param process: The process to filter by.
    :param scenario: The scenario to filter by.
    :param period: The period to filter by.
    :param dataframe: The DataFrame to filter.
    :param commodity_units: Dictionary of commodity units.
    :param filter_to_commodities: List of commodities to filter to.

    :return: A DataFrame of end-use fractions.
    """
    trace_result = trace_commodities(process, scenario, period, dataframe, commodity_units)
    # Ensure the sum of all terminal fractions is approximately 1
    assert abs(sum(trace_result.values()) - 1) < 1e-5
    end_use_fracs = pd.DataFrame(
        [
            {
                "Scenario": scenario,
                "Attribute": "VAR_FOut",
                "Commodity": None,
                "Process": process,
                "Period": period,
                "Value": None,
            }
            for process in end_use_processes
        ]
    )
    # Loop through the trace_result dictionary
    for key, value in trace_result.items():
        process_chain = key  # This is the tuple containing the process chain
        fuel_source_process = process_chain[
            0
        ]  # First entry which is the fuel source process
        process = process_chain[-2]  # Penultimate entry which is the process
        commodity = process_chain[1]  # Second entry which is the commodity
        end_use_fracs.loc[end_use_fracs["Process"] == process, "Value"] = value
        end_use_fracs.loc[end_use_fracs["Process"] == process, "Commodity"] = (
            commodity
        )
        end_use_fracs.loc[
            end_use_fracs["Process"] == process, "FuelSourceProcess"
        ] = fuel_source_process
    if filter_to_commodities is not None:
        end_use_fracs = end_use_fracs[
            (end_use_fracs["Commodity"].isin(filter_to_commodities))
            | (end_use_fracs["Commodity"].isna())
        ]
    end_use_fracs.Value = end_use_fracs.Value / end_use_fracs.Value.sum()
    return end_use_fracs


def fix_multiple_fout(dataframe):
    """
    Fix multiple VAR_FOut rows for a single VAR_FIn row

    :param dataframe: DataFrame to fix multiple VAR_FOut rows for a single VAR_FIn row.

    :return: DataFrame with multiple VAR_FOut rows for a single VAR_FIn row fixed.
    """
    filtered_df = dataframe[
        (dataframe["Attribute"] == "VAR_FOut") & (~dataframe["Commodity"].str.contains("CO2"))
    ]
    multi_fout = filtered_df.groupby(["Scenario", "Process", "Period"]).filter(
        lambda x: len(x) > 1
    )
    unique_scenario_process_periods = multi_fout[
        ["Scenario", "Process", "Period"]
    ].drop_duplicates()
    for _, row in unique_scenario_process_periods.iterrows():
        scen = row["Scenario"]
        process = row["Process"]
        period = row["Period"]
        logging.info(
            "Processing Scenario: %s, Process: %s, Period: %s",
            scen, process, period
        )
        # Filter relevant rows for the current process and period
        relevant_rows = dataframe[
            (dataframe["Scenario"] == scen)
            & (dataframe["Process"] == process)
            & (dataframe["Period"] == period)
        ]
        fin_row = relevant_rows[relevant_rows["Attribute"] == "VAR_FIn"]
        assert (
            len(fin_row) == 1
        )  # There should only be one VAR_FIn row - currently not handling multiple VAR_FIn rows
        fout_rows = relevant_rows[relevant_rows["Attribute"] == "VAR_FOut"]
        if not fin_row.empty:
            total_output = fout_rows["Value"].sum()
            ratios = fout_rows["Value"] / total_output
            # Create new VAR_FIn rows by multiplying the original Value with each ratio
            new_fin_rows = (
                fin_row.copy()
                .loc[fin_row.index.repeat(len(fout_rows))]
                .reset_index(drop=True)
            )
            new_fin_rows["Value"] = fin_row["Value"].values[0] * ratios.values
            new_fin_rows["Enduse"] = fout_rows["Enduse"].values
            # Replace the original VAR_FIn row with the new rows in the DataFrame
            dataframe = dataframe.drop(fin_row.index)  # Remove original VAR_FIn row
            dataframe = pd.concat([dataframe, new_fin_rows], ignore_index=True)
    return dataframe


def apply_rulesets(dataframe, rulesets, subset_name=None):
    """
    Complete the dataframe using the usual
    rules, taking care not to overwrite the Fuel

    :param dataframe: DataFrame to apply rules to.
    :param rulesets: List of rulesets to apply.

    :return: DataFrame with rules applied.
    """
    for name, ruleset in rulesets:
        logging.info(f"Applying ruleset to '{subset_name}' rows: %s", name)
        dataframe = apply_rules(dataframe, ruleset)
    return dataframe


def allocate_to_enduse_processes(
    rows_to_reallocate, main_df, commodity_units, filter_to_commodities=None
):
    """
    Allocate flows to end-use processes

    :param rows_to_reallocate: DataFrame containing rows to reallocate.
    :param main_df: DataFrame to reallocate rows from.
    :param commodity_units: Dictionary of commodity units.
    :param filter_to_commodities: List of commodities to filter to.

    :return: DataFrame with reallocated rows.
    """
    rows_to_add = pd.DataFrame()
    for _, row in rows_to_reallocate.iterrows():
        # For each process in question, follow
        # its outputs through to end uses;
        # get the fractional attributions of the
        # process output to end-use processes
        if filter_to_commodities is not None:
            end_use_allocations = end_use_fractions(
                row["Process"],
                row["Scenario"],
                row["Period"],
                main_df,
                commodity_units,
                filter_to_commodities=filter_to_commodities,
            )
        else:
            end_use_allocations = end_use_fractions(
                row["Process"], row["Scenario"], row["Period"], main_df, commodity_units
            )
        # Proportionately attribute the 'neg-emissions' to the end-uses, in units of Mt CO₂/yr
        end_use_allocations["Value"] *= row["Value"]
        # Tidy up and add the new rows to emissions_rows_to_add
        end_use_allocations = end_use_allocations[~end_use_allocations["Value"].isna()]
        # end_use_allocations = add_missing_columns(end_use_allocations, OUT_COLS)
        rows_to_add = pd.concat([rows_to_add, end_use_allocations], ignore_index=True)
    return rows_to_add


def fixup_emissions_attributed_to_emitting_fuels(dataframe):
    """
    Fix emissions attributed to non-emitting fuels

    :param dataframe: DataFrame to fix emissions attributed to non-emitting fuels.

    :return: DataFrame with emissions attributed to non-emitting fuels fixed.
    """
    processes_to_fix = dataframe[
        (dataframe["Fuel"].isin(constants.NON_EMISSION_FUEL)) &
        (dataframe["Parameters"] == "Emissions")
    ].Process.unique()
    for process in processes_to_fix:
        process_clean_fuel = dataframe.loc[
            (dataframe["Fuel"].isin(constants.NON_EMISSION_FUEL))
            & (dataframe["Parameters"] == "Emissions")
            & (dataframe["Process"] == process),
            "Fuel",
        ].unique()[0]
        process_all_fuels = dataframe.loc[dataframe["Process"] == process, "Fuel"].unique()
        assert any(
            fuel not in constants.NON_EMISSION_FUEL for fuel in process_all_fuels
        ), "No emitting fuel found in the process."
        process_emitting_fuel = next(
            (fuel for fuel in process_all_fuels if fuel not in constants.NON_EMISSION_FUEL), None
        )
        indices_to_update = (
            (dataframe["Fuel"] == process_clean_fuel)
            & (dataframe["Parameters"] == "Emissions")
            & (dataframe["Process"] == process)
        )
        dataframe.loc[indices_to_update, "Fuel"] = process_emitting_fuel
        dataframe.loc[indices_to_update, "FuelGroup"] = "Fossil Fuels"
    return dataframe


def complete_expand_dim(dataframe, expand_dim, fill_value_dict):
    """
    Complete the DataFrame by expanding the specified dimension

    :param dataframe: DataFrame to expand.
    :param expand_dim: Dimension to expand.

    :return: DataFrame with the specified dimension expanded.

    :raises AssertionError: If the DataFrame contains NaN values.
    """
    original_column_order = dataframe.columns
    # This implementation assumes no NaN values
    # in the starting DataFrame
    assert not dataframe.isnull().values.any(), "DataFrame contains NaN values"
    # Get all columns except the one to expand
    defcols = [expand_dim] + list(fill_value_dict.keys())
    columns = [x for x in dataframe.columns if x not in defcols]
    # Form a DataFrame with all combinations of the
    # unique values of the other dimensions
    _df = dataframe.copy().drop(columns=defcols).drop_duplicates()
    _df["key"] = 1
    # Get all unique values for the expansion dimension
    # Create a DataFrame with all expand_dim values
    # and the same key
    expand_values = dataframe[expand_dim].unique()
    expand_df = pd.DataFrame({expand_dim: expand_values, "key": 1})
    # Combine the unique values of the expand_dim
    # with the original DataFrame using the key
    # This creates a DataFrame where each row of the
    # original is repeated for each unique value of
    # the expand_dim
    df_expanded = pd.merge(_df, expand_df, on="key").drop(columns="key")
    # Merge the expanded DataFrame with the original
    # DataFrame to fill in the missing values
    df_full = pd.merge(df_expanded, dataframe, on=columns + [expand_dim], how="left")
    # for each column in fill_value_dict, fill in
    # the missing values with the specified default
    for col, fill_value in fill_value_dict.items():
        df_full[col] = df_full[col].fillna(fill_value)
    return df_full[original_column_order]


# pylint: disable=too-many-arguments
def sanity_check(subset, full_df, match_columns, tolerance, factor=1, name=""):
    """
    Conduct a sanity check to ensure that the sum of the
    values in the subset DataFrame matches the sum of the
    values in the full DataFrame for the specified columns.

    :param subset: DataFrame to check.
    :param full_df: DataFrame to check against.
    :param match_columns: Columns to match on.
    :param tolerance: Tolerance for the check.
    :param factor: Factor to multiply the subset values by.

    :return: None

    :raises AssertionError: If the sum of the values in the
        subset DataFrame does not match the sum of the values
        in the full DataFrame for the specified columns.
    """
    grouped_subset_values = subset.groupby(["Scenario", "Period"]).Value.sum()
    for (scenario, period), value in grouped_subset_values.items():
        conditions = [(full_df.Scenario == scenario), (full_df.Period == period)]
        for col, values in match_columns.items():
            if isinstance(values, list):
                condition = full_df[col].isin(values)
            else:
                condition = full_df[col] == values
            conditions.append(condition)
        final_condition = reduce(np.logical_and, conditions)
        rows_in_dataframe = full_df[final_condition]
        assert (
            abs(rows_in_dataframe.Value.sum() * factor - value) < tolerance
        ), "Value does not match within tolerance"
        logging.info(
            "Check %s output matches for Scenario: %s, Period: %s, Summed Value: %.2f: OK",
            name, scenario, period, value
        )

def check_enduse_rows(dataframe):
    """
    Check for missing values in the end-use rows

    :param dataframe: DataFrame to check.
    :return: None

    :raises AssertionError: If any missing values are found.
    """
    enduse_df = dataframe.loc[
        (dataframe.ProcessSet == ".DMD.") |
        (dataframe.CommoditySet == ".DEM.")
    ]
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
    assert (
        nan_technology_group.empty
    ), f"Missing Technology_Group {nan_technology_group}"
    assert nan_process_set.empty, f"Missing ProcessSet {nan_process_set}"
    assert nan_commodity_set.empty, f"Missing CommoditySet {nan_commodity_set}"
    assert nan_value.empty, f"Missing Value {nan_value}"


def check_missing_tech(dataframe, schema_technology):
    """
    Check for missing technologies in the DataFrame

    :param dataframe: DataFrame to check.
    :param schema_technology: List of technologies to check against.
    :return: None

    :raises ValueError: If any missing technologies are found.
    """
    enduse_df = dataframe.loc[
        (dataframe.ProcessSet == ".DMD.") |
        (dataframe.CommoditySet == ".DEM.")
    ]
    elegen_df = dataframe.loc[
        (dataframe.Sector == "Electricity") &
        (dataframe.ProcessSet == ".ELE.")
    ]
    elefue_df = dataframe.loc[
        (dataframe.Sector == "Other") &
        (dataframe.Parameters == "Fuel Consumption")
    ]
    missing_tech = enduse_df.loc[
        ~enduse_df.Technology.isin(schema_technology["Technology"])
    ]
    if not missing_tech.empty:
        raise ValueError(
            f"Missing Technologies found: {missing_tech.Technology.unique()}"
        )
    missing_tech = elegen_df.loc[
        ~elegen_df.Technology.isin(schema_technology["Technology"])
    ]
    if not missing_tech.empty:
        raise ValueError(
            f"Missing Technologies found: {missing_tech.Technology.unique()}"
        )
    missing_tech = elefue_df.loc[
        ~elefue_df.Technology.isin(schema_technology["Technology"])
    ]
    if not missing_tech.empty:
        raise ValueError(
            f"Missing Technologies found: {missing_tech.Technology.unique()}"
        )


def check_electricity_fuel_consumption(dataframe):
    """
    Check that electricity fuel consumption is only from
    electricity generation processes

    :param dataframe: DataFrame to check.
    :return: None

    :raises AssertionError: If electricity fuel consumption is not just from
        electricity generation processes.
    """
    electricity_rows = dataframe[dataframe["Sector"] == "Other"]
    electricity_fuel_consumption = electricity_rows[
        (electricity_rows["Parameters"] == "Fuel Consumption")
    ]
    assert electricity_fuel_consumption.loc[
        electricity_fuel_consumption.Attribute == "VAR_FIn"
    ].ProcessSet.unique().tolist() == [
        ".ELE."
    ], "Electricity fuel consumption not just from Electricity generation processes"


def negated_rows(dataframe, rules):
    """
    Create a new DataFrame with negated values
    and with the rows updated based on the rules
    provided.

    :param dataframe: DataFrame to negate.
    :param rules: Rules to apply to the DataFrame.
    :return: DataFrame with negated values.
    """
    neg_df = dataframe.copy()
    neg_df["Value"] = -neg_df["Value"]
    neg_df = apply_rules(neg_df, rules)
    return neg_df


def spread_to_all_aviation(drop_in_jet_domestic_rows_to_add, main_df):
    """
    Inherited from earlier data processing - create a copy to share DIJ
    consumption between domestic and international jet travel
    Split the drop-in-jet between domestic and international jet
    travel pro-rata by scenario and period. A better approach might be
    to implement this within TIMES instead of post-processing.

    :param drop_in_jet_domestic_rows_to_add:
        DataFrame containing the drop-in-jet rows to add.
    :param main_df:
        DataFrame containing the main data.

    :return: DataFrame containing the drop-in-jet rows to add.
    """
    drop_in_jet_international_rows_to_add = drop_in_jet_domestic_rows_to_add.copy()
    drop_in_jet_international_rows_to_add["Value"] = 0
    drop_in_jet_international_rows_to_add["Enduse"] = "International Aviation"
    drop_in_jet_international_rows_to_add["Process"] = "T_O_FuelJet_Int"
    for index, row in drop_in_jet_domestic_rows_to_add.iterrows():
        domestic_jet_travel = process_output_flows(
            "T_O_FuelJet", row["Scenario"], row["Period"], main_df
        )["T_O_JET"]
        internat_jet_travel = process_output_flows(
            "T_O_FuelJet_Int", row["Scenario"], row["Period"], main_df
        )["T_O_JET_Int"]
        domestic_jet_value = (
            row["Value"]
            * domestic_jet_travel
            / (internat_jet_travel + domestic_jet_travel)
        )
        internat_jet_value = (
            row["Value"]
            * internat_jet_travel
            / (internat_jet_travel + domestic_jet_travel)
        )
        drop_in_jet_domestic_rows_to_add.loc[index, "Value"] = domestic_jet_value
        drop_in_jet_international_rows_to_add.loc[index, "Value"] = internat_jet_value
    drop_in_jet_rows_to_add = pd.concat(
        [drop_in_jet_domestic_rows_to_add, drop_in_jet_international_rows_to_add],
        ignore_index=True,
    )
    return drop_in_jet_rows_to_add
