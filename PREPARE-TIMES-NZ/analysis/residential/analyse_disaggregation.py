"""
Here we just pull some intermediate outputs from the space heating model 
and make some graphs about it 

pylint doesn't check these scripts

"""
from plotnine import ggplot, aes, geom_col, facet_wrap, coord_flip, scale_fill_manual, labs, scale_y_continuous, theme_minimal
from mizani.formatters import percent_format
import pandas as pd

from prepare_times_nz.utilities.filepaths import STAGE_1_DATA, STAGE_2_DATA, ANALYSIS
from prepare_times_nz.utilities.logger_setup import logger


BASE_YEAR = 2023
OUTPUT_LOCATION = ANALYSIS / "results/residential_demand_disaggregation"
OUTPUT_LOCATION.mkdir(parents = True, exist_ok= True)

RES_DATA = STAGE_2_DATA / "residential"
RES_CHECKS = RES_DATA / "checks"

EEUD_FILE = STAGE_1_DATA / "eeud/eeud.csv"

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

def plot_disaggregation_results(category = "Fuel", end_use = "Low Temperature Heat (<100 C), Space Heating", label = "Space Heating"):

    disag_demand = pd.read_csv(RES_DATA / "residential_demand_disaggregated.csv")
    disag_demand = disag_demand[disag_demand["EndUse"] == end_use]


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
    disag_demand["Area"] = pd.Categorical(disag_demand["Area"], categories=region_order_flipped, ordered=True)
    
    # fuel orders/colours     
    fuel_config = {
        "Coal": "#000000",       
        "Wood": "#228B22",      
        "Electricity": "#6BAED6",       
        "Natural Gas": "#CC5500",
        "LPG": "#FFA500",    
    }   

    disag_demand["Fuel"] = pd.Categorical(
        disag_demand["Fuel"],
        categories=list(fuel_config.keys()),
        ordered=True
    )

    disag_demand["Value"] = disag_demand["Value"] / 1e3 # convert PJ

    chart = (
        ggplot(disag_demand, 
               aes(y = "Value", x = "Area", fill = category))
               + geom_col() 
               + facet_wrap("~DwellingType", scales = "free_x")
               + coord_flip()
               + scale_fill_manual(values=fuel_config)
               + labs(x = "Region", y = "PJ", fill = category, title = f"2023 residential {label} demand")               
               + theme_minimal()               
               )
    

    chart_name = f"demand_by_{category.lower()}_{label}.png"
    chart.save(OUTPUT_LOCATION / chart_name, dpi = 300, height= 5, width = 8)




def main():
    plot_heating_shares()
    plot_disaggregation_results("Fuel", end_use = "Low Temperature Heat (<100 C), Space Heating", label = "space heating")
    plot_disaggregation_results("Fuel", end_use = "Low Temperature Heat (<100 C), Water Heating", label = "water heating")
    plot_disaggregation_results("Fuel", end_use = "Intermediate Heat (100-300 C), Cooking", label = "cooking")
    # plot_final_results("Technology") # not much extra info here - just hp breakdown
    

if __name__ == "__main__":
    main()