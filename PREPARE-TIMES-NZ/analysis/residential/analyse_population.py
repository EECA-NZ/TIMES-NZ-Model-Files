
from plotnine import *
from mizani.formatters import percent_format
import pandas as pd

from prepare_times_nz.utilities.filepaths import STAGE_1_DATA, ANALYSIS
from prepare_times_nz.utilities.logger_setup import logger


# all we want right now is to get a chart of the current + projected population

CURRENT_POP_FILE = STAGE_1_DATA / "statsnz/estimated_resident_population.csv"
PROJECTED_POP_FILE = STAGE_1_DATA / "statsnz/projections_national_2024.csv"

OUTPUT_LOCATION = ANALYSIS / "results/population_projections"
OUTPUT_LOCATION.mkdir(parents = True, exist_ok= True)

MAX_YEAR = 2050



df = pd.read_csv(CURRENT_POP_FILE)
df = df[df["Area"] == "New Zealand"]
df["Scenario"] = "Historical"
df["Variable"] = "ERP 2024-base"

df_current = df.copy()

df = pd.read_csv(PROJECTED_POP_FILE)
df["Area"] = "New Zealand"

# df = df[df["Year"] != 2024] # remove projection of historical year 
df_projected = df.copy()

df = pd.concat([df_current, df_projected])

# make value millions 

df["Value"] = df["Value"]/1e6

# filter some scenarios
scenarios = [
    'Historical' ,
    # '5th percentile',
    '50th percentile (median)',
    # '95th percentile' 
]
df = df[df["Scenario"].isin(scenarios)]

# filter max year 

df = df[df["Year"] <= MAX_YEAR]

df["ValueLabel"] = df["Value"].astype(str) + "m"

# latest_year 

# chart 
chart = (
        ggplot(df,aes(y = "Value", x = "Year"))
               + geom_line(aes(colour = "Scenario")) 
               + geom_text(aes(label = "Value"),
                           data = df[df["Year"] == MAX_YEAR],
                           ) 
                           
               # + facet_wrap("~DwellingType", scales = "free_x")
               # + coord_flip()
               # + scale_fill_manual(values=fuel_config)
               + scale_y_continuous(limits = [0,8])
               + labs(x = "Year", y = "Population (millions)", colour = "Scenario", title = "Residential growth projections")               
               + theme_minimal()               
               )
    

chart_name = "population_projections.png"
chart.save(OUTPUT_LOCATION / chart_name, dpi = 300, height= 5, width = 8)

print(df_current)
