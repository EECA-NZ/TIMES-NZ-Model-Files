
"""


It then tidies the variableslong ways after defining the topology, setting units etc.

This is the final output for the industrial sector base year, and includes all the categories etc (so we can make concordances out of this too)

"""
import sys 
import os 
import pandas as pd 
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt


current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "../../..", "library"))
from filepaths import STAGE_2_DATA, ASSUMPTIONS
from logger_setup import logger, h1, h2 

# Filepaths --------

STAGE_2_INDUSTRY_DATA = f"{STAGE_2_DATA}/industry"
INDUSTRY_ASSUMPTIONS = f"{ASSUMPTIONS}/industry_demand"

checks_location = f"{STAGE_2_INDUSTRY_DATA}/checks"
os.makedirs(checks_location, exist_ok = True)

# Constants --------------------------------------------

# If print_charts, this script renders several results of different forecast methods

# Currently it does nothing else, but can be expanded to our eventual scenario demand forecasts 
print_charts = False 

if print_charts: 
    logger.info("Printing different forecast result charts")
else: 
    logger.info("Not currently returning forecast industrial demand - this script is WIP")

# Get data ---------------------------------------------------


def get_demand_settings():

    df = pd.read_csv(f"{INDUSTRY_ASSUMPTIONS}/sector_demand_methods.csv")
    return df

def get_aggregate_data():
    df = pd.read_csv(f"{STAGE_2_INDUSTRY_DATA}/checks/1_sector_alignment/times_eeud_alignment_timeseries.csv")
    df = df.groupby(["Year", "Sector"])["Value"].sum().reset_index()
    return df 

# Functions 

#

def make_linear_model(df):

    results = {}


    for sector, group in df.groupby("Sector"):
        group = group.sort_values("Year")
        x = group["Year"].values
        y = group["Value"].values
        # polyfit with degree 1 for linear
        slope, intercept = np.polyfit(x, y, 1)
        y_pred = slope * x + intercept

        # calc adjusted r_squared        
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r2 = 1 - (ss_res / ss_tot)

        n = len(y)
        p = 1  # number of predictors
        adj_r2 = 1 - (1 - r2) * (n - 1) / (n - p - 1)


        results[sector] = {            
            "slope": slope,
            "intercept": intercept,
            "r2": r2,
            "adj_r2": adj_r2
            }             

    
    return results


def carry_forward_linear(df, final_year = 2050):
    regression = make_linear_model(df)
    future_years = np.arange(df["Year"].min(), final_year)
    preds = []


    for sector, params in regression.items():
        slope = params["slope"]
        intercept = params["intercept"]
        adj_r2 = params["adj_r2"]
        for year in future_years:
            demand_pred = slope * year + intercept
            preds.append({"Sector": sector,
                          "Year": year,
                          "predicted_demand": demand_pred,
                          "adj_r2" : adj_r2,
                          })


    future_df = pd.DataFrame(preds)

    return future_df


# some data standardising to join real and actual 
def reshape_preds(df):
    df = df[["Year", "Sector", "predicted_demand"]]
    df = df.rename(columns={"predicted_demand": "Value"})
    df["Type"] = "Predicted"

    return df 

def reshape_actuals(df): 
    df = df[["Year", "Sector", "Value"]]
    df["Type"] = "Actual"

    return df 

def calc_cagr(start_value, end_value, num_years):
    if start_value == 0 or num_years == 0:
        return np.nan
    return (end_value / start_value) ** (1 / num_years) - 1

def get_cagrs(df):

    cagrs = []

    for sector, group in df.groupby("Sector"):
        group = group.sort_values("Year")
        start_val = group["Value"].iloc[0]
        end_val = group["Value"].iloc[-1]
        years = group["Year"].iloc[-1] - group["Year"].iloc[0]

        cagr = calc_cagr(start_val, end_val, years)
        cagrs.append({"Sector": sector, 
                      "StartValue": start_val,
                      "EndValue": end_val,
                      "years": years,
                      # "EndValue": end_val,
                      "CAGR": cagr})

        cagr_df = pd.DataFrame(cagrs)

    return cagr_df 

def forecast_cagr(last_year, last_value, cagr, end_year):
    years = np.arange(last_year + 1, end_year + 1)
    preds = []

    for i, year in enumerate(years, 1):  # start at 1 year after
        value = last_value * ((1 + cagr) ** i)
        preds.append({'Year': year, 'predicted_demand': value})
    
    return pd.DataFrame(preds)

def cast_with_cagr(df, final_year = 2050, method = "normal"):  


    """
    Expect Year, Sector, Value from historical data     
    """

    df_cagrs = get_cagrs(df)
    df_cagrs = df_cagrs[["Sector", "CAGR"]]

    df = pd.merge(df, df_cagrs, on = "Sector", how = "left")

    all_preds = []

    for sector in df["Sector"].unique():

        df_sector = df[df['Sector'] == sector]
        row = df_sector.iloc[0]
        last_val = df_sector.sort_values('Year')['Value'].iloc[-1]
        last_year = df_sector['Year'].max()
        cagr = row['CAGR']

        energy_preds = forecast_cagr(last_year, last_val, cagr, final_year)
        energy_preds["Sector"] = sector

        all_preds.append(energy_preds)


    return pd.concat(all_preds, ignore_index=True)

def get_historical_linear_values(df):

    historical_df = df

    df = carry_forward_linear(historical_df)
    df = reshape_preds(df)
    df = df.drop("Type", axis = 1)

    historical_years = historical_df["Year"].unique()

    df = df[df['Year'].isin(historical_years)]


    return df

def make_forecast_chart(df, method = "Linear Regression"):
    # regress and cast results 

    # standardise predictions and actuals 

    logger.info(f"Forecasting demand with {method}")

    if method == "Linear Regression":        
        preds_raw = carry_forward_linear(df)
        preds = reshape_preds(preds_raw)
    
    if method == "CAGR":        
        preds_raw = cast_with_cagr(df)
        cagrs = get_cagrs(df)
        preds = reshape_preds(preds_raw)

    if method == "CAGR (smooth historical)":        
        linear_historical = get_historical_linear_values(df) 
        cagrs = get_cagrs(linear_historical)
        preds_raw = cast_with_cagr(linear_historical)
        preds = reshape_preds(preds_raw)

    actuals = reshape_actuals(df)

    # add the results to main df
    df = pd.concat([actuals, preds])
    

    sns.set_style("whitegrid")

    # facet plot that shows demand per sector over time
    g = sns.FacetGrid(df, col="Sector", hue = "Type", col_wrap=4, sharey=False)
    g.map(sns.lineplot, "Year", "Value")

    
    for ax in g.axes.flat:
        ax.set_ylim(bottom=0)

    plt.suptitle(f'Demand Forecasts by Sector ({method})', fontsize=14)
    plt.tight_layout(rect=[0, 0, 1, 0.95])  # leave space for the title

    if method in ["CAGR", "CAGR (smooth historical)"]:
        cagr_map = {
            row['Sector']: f"{row['Sector']}({row['CAGR'] * 100:.1f}%)"
            for _, row in cagrs.iterrows()
        }

        # now use that in the grid
        def custom_title(col_name):
            return cagr_map.get(col_name, col_name)

        g.set_titles(col_template="{col_name}")  # base template
        for ax, title in zip(g.axes.flat, g.col_names):
            ax.set_title(custom_title(title))

    else:
        g.set_titles(col_template="{col_name}")

    plt.tight_layout()

    chart_location = f'{checks_location}/demand_forecast_{method.lower().replace(" ", "_")}.png'
    logger.info(f"Saving results to {chart_location}")
    plt.savefig(chart_location, dpi=300)
    
df = get_aggregate_data()

if print_charts:
    make_forecast_chart(df, method = "Linear Regression")
    make_forecast_chart(df, method = "CAGR")
    make_forecast_chart(df, method = "CAGR (smooth historical)")

