import os

import pandas as pd
from prepare_times_nz.data_cleaning import rename_columns_to_pascal
from prepare_times_nz.filepaths import DATA_RAW, STAGE_1_DATA

# FILEPATHS -------------------------------------------------------------------------
input_location = f"{DATA_RAW}/external_data/gic"
output_location = f"{STAGE_1_DATA}/gic"
os.makedirs(output_location, exist_ok=True)

gic_filename = "ProductionConsumption.xlsx"


def read_gic_data(SheetName):
    gic_location = f"{input_location}/{gic_filename}"
    df = pd.read_excel(gic_location, sheet_name=SheetName)
    return df


def get_all_gic_data():
    df1 = read_gic_data("Prod_Cons")
    df2 = read_gic_data("Rep Major Users")
    # want everything even if the join fails left or right (it shouldn't but we carry on if it does )
    df = pd.merge(df1, df2, on="Date")
    return df


def pivot_gic_data(df):
    df = pd.melt(df, id_vars="Date", var_name="Participant", value_name="Value")
    return df


def define_producers_and_consumers(df):
    """
    Here we manually list the producers in the producer/consumer list
    I don't think this is super important since we're really just using this data for the Ballance/Methanex splits?
    But we're doing it here anyway just in case
    """

    # Set default
    df["UserType"] = "Consumer"

    producers = [
        # Here we manually list the GIC producers from the producer/consumer list
        "Pohokura",
        "Maui",
        "McKee/Mangahewa",
        "Turangi and Kowhai",
        "Kupe",
        "Kapuni",
        "Kaimiro",
        "Mokoia",
        "Cheal",
        "Sidewinder",
    ]

    # Change label for producers
    df.loc[(df["Participant"].isin(producers)), "UserType"] = "Producer"

    return df


def label_and_rearrange_gic_data(df):
    df["Unit"] = "TJ"

    df = df[["Date", "UserType", "Participant", "Unit", "Value"]]

    return df


# run

df = get_all_gic_data()
df = pivot_gic_data(df)
df = define_producers_and_consumers(df)
df = label_and_rearrange_gic_data(df)

df.to_csv(f"{output_location}/gic_production_consumption.csv", index=False)

# print(df)
