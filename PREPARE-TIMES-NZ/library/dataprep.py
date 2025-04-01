# The plan for this script is to make a function that can handle all of the data in csv files and then spit out all the INVCOST for the new tech files
import numpy as np
import pandas as pd



def filter_csv_by_multiple_columns(df, filters, output_filtered_file=None, output_excluded_file=None):
    """
    Reads a CSV file and filters rows based on values in multiple specified columns.
    
    Parameters:
    - file_path (str): Path to the input CSV file.
    - filters (dict): A dictionary where keys are column names and values are the values to keep.
                      Values can be a string (single value) or a list of values.
    - output_filtered_file (str, optional): Path to save the filtered-in CSV (default: None).
    - output_excluded_file (str, optional): Path to save the filtered-out CSV (default: None).
    
    Returns:
    - tuple: (filtered_df, excluded_df) where:
      - filtered_df (pandas.DataFrame): The DataFrame containing rows that match the filters.
      - excluded_df (pandas.DataFrame): The DataFrame containing rows that do not match the filters.
    """
    try:
        
        # Create a boolean mask to track filtered rows
        mask = pd.Series(True, index=df.index)
        
        # Apply multiple filters (AND logic: all conditions must be met)
        for column, filter_values in filters.items():
            if column not in df.columns:
                raise ValueError(f"Column '{column}' not found in CSV.")
            
            # Convert single values to lists
            if isinstance(filter_values, str):
                filter_values = [filter_values]
            
            # Update the mask based on this column filter
            mask &= df[column].isin(filter_values)
        
        # Split the DataFrame into filtered and excluded
        filtered_df = df[mask]
        excluded_df = df[~mask]
        
        # Save the filtered data if output files are provided
        if output_filtered_file:
            filtered_df.to_csv(output_filtered_file, index=False)
            print(f"Filtered CSV saved to {output_filtered_file}")
        
        if output_excluded_file:
            excluded_df.to_csv(output_excluded_file, index=False)
            print(f"Excluded CSV saved to {output_excluded_file}")
        
        return filtered_df, excluded_df
    
    except Exception as e:
        print(f"Error: {e}")
        return None, None

#Next we want to normalize the values

def divide_from_specific_column(df, base_column, row_conditions):
    """
    Divides columns from `base_column` (inclusive) onward by a dynamically chosen base column per row.

    Parameters:
    - df (pandas.DataFrame): A Pandas DataFrame.
    - base_column (str): The name of the column to use as the default divisor.
    - row_conditions (dict): A dictionary where keys are row indices and values are alternative column names to use as the divisor.

    Returns:
    - pandas.DataFrame: The transformed DataFrame after division.
    """
    if base_column not in df.columns:
        raise ValueError(f"Column '{base_column}' not found in DataFrame.")

    df_copy = df.copy()  # Avoid modifying the original DataFrame

    # Remove $ and commas, then convert to float
    df_copy.loc[:, base_column:] = (
        df_copy.loc[:, base_column:]
        .replace({r"[^\d.]": ""}, regex=True)  # Removes everything except numbers and decimal points
        .astype(float)  # Convert to float
    )

    # Default division using the base_column
    df_copy.loc[:, base_column:] = df_copy.loc[:, base_column:].div(df_copy[base_column], axis=0)

    # Apply row-specific alternative base columns
    for row_idx, alt_column in row_conditions.items():
        if alt_column not in df.columns:
            raise ValueError(f"Column '{alt_column}' not found in DataFrame.")
        
        # Ensure alternative divisor is not NaN before division
        divisor = df_copy.loc[row_idx, alt_column]
        if pd.isna(divisor) or divisor == 0:
            print(f"Warning: Row {row_idx} has invalid divisor ({divisor}). Skipping division for this row.")
            continue

        df_copy.loc[row_idx, base_column:] = df_copy.loc[row_idx, base_column:].div(divisor)

    return df_copy


def filter_csv_by_one_column(df, column_name, filter_values, output_filtered_file=None):
    """
    Reads a CSV file and filters rows based on values in a single specified column.
    
    Parameters:
    - file_path (str): Path to the input CSV file.
    - column_name (str): The column name to filter by.
    - filter_values (str or list): The values to keep in the filtered DataFrame.
    - output_filtered_file (str, optional): Path to save the filtered CSV (default: None).
    
    Returns:
    - pandas.DataFrame: The DataFrame containing rows that match the filter.
    """
    try:
        # Check if the column exists
        if column_name not in df.columns:
            raise ValueError(f"Column '{column_name}' not found in CSV.")
        
        # Convert single values to a list
        if isinstance(filter_values, (str, int, float)):
            filter_values = [filter_values]
        
        # Create mask for filtering
        filtered_df = df[df[column_name].isin(filter_values)].copy()
        
        # Save to CSV if an output file is specified
        if output_filtered_file:
            filtered_df.to_csv(output_filtered_file, index=False)
            print(f"Filtered CSV saved to {output_filtered_file}")
        
        return filtered_df
    
    except Exception as e:
        print(f"Error: {e}")
        return None


def filter_and_move_rows(varied_cost, fixed_cost, column_name, threshold=2030):
    """
    Filters `varied_cost` to remove rows where the specified column has values 
    greater than 0 but less than the threshold (default 2030), and moves those rows 
    to `fixed_cost`. Rows with values >= threshold, 0, or NaN remain in `varied_cost`.

    Parameters:
    - varied_cost (pandas.DataFrame): The DataFrame to filter.
    - fixed_cost (pandas.DataFrame): The DataFrame to receive the removed rows.
    - column_name (str): The column used for filtering.
    - threshold (int, optional): The cutoff value for filtering (default: 2030).

    Returns:
    - tuple: (updated_varied_cost, updated_fixed_cost)
    """
    try:
        # Make a copy to avoid modifying the original DataFrame
        varied_cost = varied_cost.copy()
        
        # Convert the column to numeric, setting errors as NaN
        varied_cost[column_name] = pd.to_numeric(varied_cost[column_name], errors='coerce')
        
        # Create mask for rows to move: value > 0 and < threshold
        move_mask = (varied_cost[column_name] > 0) & (varied_cost[column_name] < threshold)
        
        # Move those rows to fixed_cost
        fixed_cost = pd.concat([fixed_cost, varied_cost.loc[move_mask]], ignore_index=True)
        
        # Keep only the other rows in varied_cost
        varied_cost = varied_cost.loc[~move_mask].copy()
        
        return varied_cost, fixed_cost

    except Exception as e:
        print(f"Error: {e}")
        return None, None



def filter_by_column(varied_cost, column_name, keep_values, fixed_cost):
    """
    Filters `varied_cost` by keeping only rows where `column_name` contains one of the `keep_values`,
    and appends the removed rows to `fixed_cost`.

    Parameters:
    - varied_cost (pandas.DataFrame): The DataFrame to filter.
    - column_name (str): The column used for filtering.
    - keep_values (list): A list of values to keep in `varied_cost`.
    - fixed_cost (pandas.DataFrame): DataFrame where removed rows will be appended.

    Returns:
    - tuple: (updated_varied_cost, updated_fixed_cost)
    """
    try:
        # Create mask for rows to keep
        keep_mask = varied_cost[column_name].isin(keep_values)

        # Identify rows to move
        rows_to_move = varied_cost.loc[~keep_mask].copy()

        # Update varied_cost with rows to keep
        varied_cost = varied_cost.loc[keep_mask].copy()

        # Append removed rows to fixed_cost
        fixed_cost = pd.concat([fixed_cost, rows_to_move], ignore_index=True)

        return varied_cost, fixed_cost

    except Exception as e:
        print(f"Error: {e}")
        return None, fixed_cost


def remove_rows_by_column_value(df, column_name, remove_value):
    """
    Removes rows from a DataFrame where the specified column matches the remove_value.

    Parameters:
    - df (pandas.DataFrame): The DataFrame to filter.
    - column_name (str): The column to check for removal.
    - remove_value (str, int, float): The value to remove.

    Returns:
    - pandas.DataFrame: The updated DataFrame after removal.
    """
    try:
        # Ensure df is a copy to avoid modifying the original
        df = df.copy()

        # Create mask to filter out rows that match the remove_value
        mask = df[column_name] != remove_value

        # Return the filtered DataFrame
        return df.loc[mask].copy()

    except Exception as e:
        print(f"Error: {e}")
        return None


def merge_specific_group(df, group_column, name_column, new_name, target_group):
    """
    Merges rows where `group_column` matches `target_group`.
    
    - Applies merging only to rows where `group_column == target_group`.
    - Modifies `name_column` to use `new_name`.
    - Keeps other columns unchanged.
    
    Parameters:
    - df (pandas.DataFrame): The DataFrame to process.
    - group_column (str): The column used to identify rows to merge.
    - name_column (str): The column to modify (e.g., "Tech Name").
    - new_name (str): The new value for `name_column` in the merged row.
    - target_group (str or int): The value of `group_column` to filter before merging.

    Returns:
    - pandas.DataFrame: The updated DataFrame with merged rows for the specific group.
    """
    try:
        # Ensure df is copied
        df = df.copy()

        # Identify rows that belong to the target group
        target_df = df[df[group_column] == target_group]
        other_df = df[df[group_column] != target_group]

        # Perform merging only on the target group
        grouped_df = target_df.groupby(group_column).first().reset_index()
        grouped_df[name_column] = new_name  # Change the name for merged rows

        # Combine merged group data with unmodified data
        merged_df = pd.concat([grouped_df, other_df], ignore_index=True)

        return merged_df

    except Exception as e:
        print(f"Error: {e}")
        return None


def remove_columns(df, columns_to_remove):
    """
    Removes specified columns from a DataFrame.

    Parameters:
    - df (pandas.DataFrame): The input DataFrame.
    - columns_to_remove (list): A list of column names to remove.

    Returns:
    - pandas.DataFrame: A new DataFrame with the specified columns removed.
    """
    try:
        # Ensure df is copied to avoid modifying the original DataFrame
        df = df.copy()
        
        # Drop specified columns (ignore errors if column not found)
        df = df.drop(columns=columns_to_remove, errors="ignore")
        
        return df
    
    except Exception as e:
        print(f"Error: {e}")
        return None
    
def combine_and_multiply_by_row(df1, df2, selected_columns, multiply_column, option_column, mapping_dict, label_from_df2, constant_col1, constant_col2):
    """
    Creates a new DataFrame using selected columns from df1, multiplies a specific column by a row in df2 
    based on a condition in df1, and adds a constant calculated as (df1[constant_col1] / df1[constant_col2]).

    Parameters:
    - df1 (pandas.DataFrame): The first DataFrame.
    - df2 (pandas.DataFrame): The second DataFrame (contains rows to map to).
    - selected_columns (list): List of column names from df1 to include in the new DataFrame.
    - multiply_column (str): Column in df1 that is multiplied by a row from df2.
    - option_column (str): Column in df1 containing a string indicating which row to use for multiplication.
    - mapping_dict (dict): Dictionary mapping string values in `option_column` to row indices in df2.
    - label_from_df2 (list): Column names from df2 to use as labels for the multiplied columns.
    - constant_col1 (str): Column in df1 used for computing the constant.
    - constant_col2 (str): Column in df1 used as the denominator in the constant calculation.

    Returns:
    - pandas.DataFrame: The resulting DataFrame.
    """
    try:
        # Select required columns from df1
        new_df = df1[selected_columns].copy()
        
        # Compute the constant (avoid division by zero)
        df1 = df1.copy()
        df1["constant"] = df1[constant_col1] / df1[constant_col2]*1000
        df1["constant"] = df1["constant"].fillna(0)  # Replace NaN values with 0 if division fails

        # Create an empty DataFrame to store multiplied values
        multiplied_values = pd.DataFrame(index=df1.index, columns=label_from_df2)

        # Iterate over rows to determine which row from df2 to use
        for idx, row in df1.iterrows():
            if row[option_column] in mapping_dict:
                selected_df2_row = df2.loc[mapping_dict[row[option_column]]]
                multiplied_values.loc[idx] = selected_df2_row * row[multiply_column]

        # Convert to numeric and replace NaNs with 0
        multiplied_values = multiplied_values.apply(pd.to_numeric, errors="coerce").fillna(0)

        # Add the constant to the multiplied values
        multiplied_values = multiplied_values.add(df1["constant"], axis=0)

        # Merge selected columns with the multiplied data
        final_df = pd.concat([new_df, multiplied_values], axis=1)

        return final_df
    
    except Exception as e:
        print(f"Error: {e}")
        return None
    
    
def combine_and_multiply_FOM(df1, df2, selected_columns, multiply_column, option_column, mapping_dict, label_from_df2, transform_func=None):
    """
    Creates a new DataFrame using selected columns from df1, multiplies a specific column by a row in df2 
    based on a condition in df1, and applies a transformation function if provided.

    Parameters:
    - df1 (pandas.DataFrame): The first DataFrame.
    - df2 (pandas.DataFrame): The second DataFrame (contains rows to map to).
    - selected_columns (list): List of column names from df1 to include in the new DataFrame.
    - multiply_column (str): Column in df1 that is multiplied by a row from df2.
    - option_column (str): Column in df1 containing a string indicating which row to use for multiplication.
    - mapping_dict (dict): Dictionary mapping string values in `option_column` to row indices in df2.
    - label_from_df2 (list): Column names from df2 to use as labels for the multiplied columns.
    - transform_func (callable, optional): A function to apply row-wise to df1 before merging (e.g., lambda x: x['A'] / x['B']).

    Returns:
    - pandas.DataFrame: The resulting DataFrame.
    """
    try:
        # Select required columns from df1
        new_df = df1[selected_columns].copy()
        
        # Apply transformation function if provided
        if transform_func:
            df1 = df1.copy()
            df1["transformed_value"] = df1.apply(transform_func, axis=1).fillna(0)

        # Create an empty DataFrame to store multiplied values
        multiplied_values = pd.DataFrame(index=df1.index, columns=label_from_df2)

        # Iterate over rows to determine which row from df2 to use
        for idx, row in df1.iterrows():
            if row[option_column] in mapping_dict:
                selected_df2_row = df2.loc[mapping_dict[row[option_column]]]
                multiplied_values.loc[idx] = selected_df2_row * row[multiply_column]

        # Convert to numeric and replace NaNs with 0
        multiplied_values = multiplied_values.apply(pd.to_numeric, errors="coerce").fillna(0)

        # If a transformation function was applied, add its result
        if transform_func:
            multiplied_values = multiplied_values.add(df1["transformed_value"], axis=0)

        # Merge selected columns with the multiplied data
        final_df = pd.concat([new_df, multiplied_values], axis=1)

        return final_df
    
    except Exception as e:
        print(f"Error: {e}")
        return None
    
def clean_and_multiply(df, const1, const2):
    df = df.copy()
    data_cols = df.columns[1:]

    for col in data_cols:
        # Use raw string to avoid warning
        df[col] = df[col].replace(r'[\$,]', '', regex=True).astype(float)
        df[col] = df[col] * const1 / const2

    return df

def assign_type(df, col1, col2):
    def get_type(row):
        val1 = row[col1]
        val2 = row[col2]

        # Check if col1 has a non-zero/non-null value
        if pd.notnull(val1) and val1 != 0:
            return "Fixed"
        # col1 is blank or zero, check col2
        elif pd.notnull(val2) and val2 != 0:
            return "Earliest year"
        else:
            return "Any year"

    df['Type'] = df.apply(get_type, axis=1)
    return df


def move_columns(df, moves):
    """
    moves: list of (col_name, new_position) tuples
    """
    cols = list(df.columns)
    
    for col_name, new_pos in moves:
        cols.insert(new_pos, cols.pop(cols.index(col_name)))
    
    return df[cols]

def conditional_row_filter(df, trigger_col, trigger_value, col1, col2):
    """
    Removes rows from `df` where:
    - df[trigger_col] == trigger_value
    - AND df[col2] < df[col1]
    
    Parameters:
    - df: pandas DataFrame
    - trigger_col: column to look for a specific string value
    - trigger_value: the string value to match
    - col1: first column in comparison
    - col2: second column in comparison (col2 < col1 triggers deletion)
    
    Returns:
    - Filtered DataFrame with rows removed
    """
    # Ensure comparison columns are numeric
    df[col1] = pd.to_numeric(df[col1], errors='coerce')
    df[col2] = pd.to_numeric(df[col2], errors='coerce')

    # Build the condition mask
    condition = (df[trigger_col] == trigger_value) & (df[col2] < df[col1])
    
    # Keep rows where the condition is NOT true
    return df[~condition].reset_index(drop=True)


def duplicate_and_modify_rows_two_conditions(
    df,
    condition_col1, trigger_values1,
    condition_col2, trigger_values2,
    str_col1, new_val1,
    str_col2, new_val2,
    nan_col
):
    """
    Duplicates rows where:
    - df[condition_col1] is in trigger_values1
    - AND df[condition_col2] is in trigger_values2

    Then modifies two string columns and sets another column to NaN.

    Returns:
        Modified DataFrame with added rows.
    """
    new_rows = []

    for _, row in df.iterrows():
        if row[condition_col1] in trigger_values1 and row[condition_col2] in trigger_values2:
            row_copy = row.copy()
            row_copy[str_col1] = new_val1
            row_copy[str_col2] = new_val2
            row_copy[nan_col] = np.nan
            new_rows.append(row_copy)

    # Add the new rows to the original DataFrame
    if new_rows:
        df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)

    return df


def assign_value_with_multiple_conditions(df, condition1_col, condition1_val,
                                          condition2_col, condition2_val,
                                          check_col, target_col, value_map):
    def logic(row):
        if (row[condition1_col] == condition1_val) and (row[condition2_col] == condition2_val):
            return value_map.get(row[check_col], row.get(target_col))
        return row.get(target_col)

    df[target_col] = df.apply(logic, axis=1)
    return df

def duplicate_rows_with_new_column(df, new_column_name, values_list):
    """
    Duplicates each row in the dataframe for each value in the values_list
    and adds a new column with those values.

    Parameters:
        df (pd.DataFrame): Original DataFrame
        new_column_name (str): Name of the new column to add
        values_list (list): List of values to insert into the new column for duplication

    Returns:
        pd.DataFrame: Expanded DataFrame with duplicated rows and new column
    """
    repeated_df = pd.concat([df.assign(**{new_column_name: value}) for value in values_list], ignore_index=True)
    return repeated_df