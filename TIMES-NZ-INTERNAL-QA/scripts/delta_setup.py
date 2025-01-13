# libraries 
import pandas as pd 

# set runs (can do this elsewhere later)

qa_runs = ["tui-v2_1_2", "tui-v2_1_3"]

run_a = qa_runs[0]
run_b = qa_runs[1]


constant_variables = ["Attribute", "Commodity", "Process", "Period", "Region"]


# get all unique combinations for each scenario

only_variables = (output_df.drop_duplicates(subset = constant_variables + ["Scenario"]))     

variables_a = only_variables[only_variables["Scenario"] == run_a].drop("Scenario", axis = 1)
variables_b = only_variables[only_variables["Scenario"] == run_b].drop("Scenario", axis = 1)


matching_variables = pd.merge(
    variables_a, variables_b, 
    on = constant_variables,
    suffixes = ("_a", "_b")
)

agg_table = (output_df
             .groupby(constant_variables + ["Scenario"])
             .sum("PV").reset_index()
)

# retain all other variables in pivot
index_cols = [col for col in agg_table.columns if col not in ["PV", "Scenario"]]

delta_test = agg_table.pivot(    
    index = index_cols,
    columns = "Scenario",
    values = "PV"
).fillna(0).reset_index()


delta_test["Delta"] = delta_test[run_a] - delta_test[run_b]

# tolerance within 0.1% change
# i thought i would need to mess around with the way it handles 0s but it seems to work fine 
delta_test["Delta_Proc"] = delta_test[run_b] / delta_test[run_a] - 1
delta_test =  delta_test[(abs(delta_test["Delta_Proc"]) > 0.001 )] 


# add concordance back 
delta_test = add_concordance_to_vd(delta_test)

#delta_test = delta_test.groupby(["Attribute", "Commodity", "Process"]).size().reset_index(name = "diff_count")

#$delta_test = add_concordance_to_vd(delta_test)

pd.set_option('display.max_rows', 10              )


changed_grain = delta_test.groupby(["Attribute", "Process", "Commodity"]).size().reset_index(name = "Count").drop("Count", axis = 1 )


delta_data = output_df.merge(changed_grain)

df = delta_data

sector_options = delta_data["Sector"].unique()
parameter_options = delta_data["Parameters"].unique()


sector_options

df["Parameters"].unique()
df.columns

# Replace NaN with "Missing" in those columns
string_columns = df.select_dtypes(include=['object']).columns
string_columns = [col for col in string_columns if col != 'PV']
df[string_columns] = df[string_columns].fillna('Missing')

sector_options = df["Sector"].unique().tolist()
parameter_options = df["Parameters"].unique().tolist()
