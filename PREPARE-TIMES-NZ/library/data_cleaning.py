import re



# Column name tidying: 

def pascal_case(name: str) -> str:
    # Split by non-word characters and camelCase boundaries
    parts = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', name)
    return ''.join(word.capitalize() for word in parts)

def rename_columns_to_pascal(df):
    new_names = [pascal_case(col) for col in df.columns]
    return df.rename(dict(zip(df.columns, new_names)))