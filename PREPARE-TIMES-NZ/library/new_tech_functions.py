#This script contains the specific functions for new_tech_data in stage 3 scenarios.
import numpy as np
import pandas as pd

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

def filter_and_move_rows(varied_cost, fixed_cost, column_name, threshold):
    """
    Filters `varied_cost` to remove rows where the specified column has values 
    greater than 0 but less than the threshold, and moves those rows 
    to `fixed_cost`. Rows with values >= threshold, 0, or NaN remain in `varied_cost`.

    Parameters:
    - varied_cost (pandas.DataFrame): The DataFrame to filter.
    - fixed_cost (pandas.DataFrame): The DataFrame to receive the removed rows.
    - column_name (str): The column used for filtering.
    - threshold (int, optional): The cutoff value for filtering.

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

def convert_label(col):
    try:
        # Try converting to integer
        return int(col)
    except ValueError:
        # If it fails, leave it as is
        return col
