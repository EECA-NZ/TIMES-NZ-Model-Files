"""
Defines the ui for the internal app
"""

import pandas as pd
from shiny import ui
from shinywidgets import output_widget
from times_nz_internal_qa.utilities.filepaths import FINAL_DATA

ele_gen_data = pd.read_csv(FINAL_DATA / "elec_generation.csv")


def get_df_options(df, variable):
    """
    returns all the options for variable in df
    as a list. useful for dynamic app selection.
    """
    df = df.copy()
    return df[variable].unique().tolist()


ele_gen_variables = get_df_options(ele_gen_data, "Variable")

ele_gen_group_options = [
    "TechnologyGroup",
    "Region",
    "PlantName",
    "Technology",
    "PlantName",
    "Fuel",
]
ele_gen_fuel_options = get_df_options(ele_gen_data, "Fuel")
app_ui = ui.page_fluid(
    ui.h2("TIMES Alpha"),
    # ele generation
    ui.h3("Electricity generation"),
    ui.layout_columns(
        ui.input_select("variable", "Select variable", ele_gen_variables),
        ui.input_select("group", "Select group", ele_gen_group_options),
    ),
    ui.span("Filters"),
    ui.layout_columns(
        ui.input_select("fuel", "Fuel", ele_gen_fuel_options),
        # ui.input_select("group", "Select group", ele_gen_group_options),
    ),
    output_widget("chart"),
)
