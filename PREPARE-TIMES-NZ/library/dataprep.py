# The plan for this script is to make a function that can handle all of the data in csv files and then spit out all the INVCOST for the new tech files
import numpy as np
import pandas as pd



def filter_df_by_multiple_columns(df, filters):
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
        
        return filtered_df, excluded_df
    
    except Exception as e:
        print(f"Error: {e}")
        return None, None

def filter_df_by_one_column(df, column_name, filter_values):
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
        
        return filtered_df
    
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

