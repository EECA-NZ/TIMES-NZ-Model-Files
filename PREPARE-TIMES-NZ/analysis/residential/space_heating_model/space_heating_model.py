"""
Here we just pull some intermediate outputs from the space heating model 
and make some graphs about it 



"""
from plotnine import ggplot, aes, geom_col, facet_wrap, coord_flip, scale_fill_manual, labs, scale_y_continuous, theme_minimal
from mizani.formatters import percent_format
import pandas as pd
import numpy as np 



from prepare_times_nz.utilities.filepaths import STAGE_2_DATA, ANALYSIS


OUTPUT_LOCATION = ANALYSIS / "results/space_heating_model"
OUTPUT_LOCATION.mkdir(parents = True, exist_ok= True)

RES_DATA = STAGE_2_DATA / "residential"
RES_CHECKS = RES_DATA / "checks"

# get data 


def plot_heating_shares():

    heating_shares = pd.read_csv(RES_CHECKS / "fuel_heating_shares.csv")

    
    region_order  = [ 
        "Northland",
        "Auckland",
        "Waikato",
        "Bay of Plenty",
        "Gisborne",
        "Hawke's Bay",
        "Taranaki",
        "Manawatū-Whanganui",
        "Wellington",
        "Tasman",
        "Nelson",
        "Marlborough",
        "West Coast",
        "Canterbury",
        "Otago",
        "Southland",
    ]
    
    
    region_order_flipped = list(reversed(region_order))
    
    heating_shares["Area"] = pd.Categorical(heating_shares["Area"], categories=region_order_flipped, ordered=True)
    
    
    
    
    heating_type_config = {
        "Coal burner": "#000000",       # black
        "Wood burner": "#006400",       # dark green
        "Pellet fire": "#228B22",       # green
        "Fixed gas heater": "#CC5500",  # darker orange
        "Portable gas heater": "#FFA500", # orange
        "Electric heater": "#00008B",   # dark blue
        "Heat pump": "#6BAED6",         # light blue
    }
    
    # Apply categorical order to your dataframe
    heating_shares["HeatingType"] = pd.Categorical(
        heating_shares["HeatingType"],
        categories=list(heating_type_config.keys()),
        ordered=True
    )
    
    chart = (
        ggplot(heating_shares, 
               aes(y = "FuelHeatingShare", x = "Area", fill = "HeatingType"))
               + geom_col() 
               + facet_wrap("~DwellingType")
               + coord_flip()
               + scale_fill_manual(values=heating_type_config)
               + labs(x = "Region", y = "Share", fill = "Heating Method", title = "Share of heating method per region and dwelling type")
               + scale_y_continuous(breaks=[0, 0.5,1.0], labels=percent_format())
               + theme_minimal()
               
               )
    
    
    chart.save(OUTPUT_LOCATION / "heating_shares.png", dpi = 300, height= 5, width = 8)

def plot_final_results(category):

    sh_demand = pd.read_csv(RES_DATA / "residential_space_heating_disaggregation.csv")


    # region orders     
    region_order  = [ 
        "Northland",
        "Auckland",
        "Waikato",
        "Bay of Plenty",
        "Gisborne",
        "Hawke's Bay",
        "Taranaki",
        "Manawatū-Whanganui",
        "Wellington",
        "Tasman",
        "Nelson",
        "Marlborough",
        "West Coast",
        "Canterbury",
        "Otago",
        "Southland",
    ]
    region_order_flipped = list(reversed(region_order))
    sh_demand["Area"] = pd.Categorical(sh_demand["Area"], categories=region_order_flipped, ordered=True)
    
    # fuel orders/colours     
    fuel_config = {
        "Coal": "#000000",       
        "Wood": "#228B22",      
        "Electricity": "#6BAED6",       
        "Natural Gas": "#CC5500",
        "LPG": "#FFA500",    
    }   

    sh_demand["Fuel"] = pd.Categorical(
        sh_demand["Fuel"],
        categories=list(fuel_config.keys()),
        ordered=True
    )

    # tech orders/colours 

    techs = [sh_demand["Technology"].unique()]

    print(techs)


    sh_demand["Value"] = sh_demand["Value"] / 1e3 # convert PJ
    # this agg actually isn't even needed huh 
    sh_demand_agg = sh_demand.groupby(["Sector", "DwellingType", "Area", category])["Value"].sum().reset_index()   




    chart = (
        ggplot(sh_demand_agg, 
               aes(y = "Value", x = "Area", fill = category))
               + geom_col() 
               + facet_wrap("~DwellingType", scales = "free_x")
               + coord_flip()
               + scale_fill_manual(values=fuel_config)
               + labs(x = "Region", y = "PJ", fill = category, title = "2023 residential space heating demand")
               # + scale_y_continuous(breaks=[0, 0.5,1.0], labels=percent_format())
               + theme_minimal()
               
               )
    

    chart_name = f"demand_by_{category.lower()}.png"
    
    
    chart.save(OUTPUT_LOCATION / chart_name, dpi = 300, height= 5, width = 8)


def main():
    plot_heating_shares()
    plot_final_results("Fuel")
    # plot_final_results("Technology") # not much extra info here - just hp breakdown


if __name__ == "__main__":
    main()