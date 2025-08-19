"""
Some charts of the load curve inputs 

Fairly scrappy
"""

from plotnine import *
from itertools import product
from mizani.formatters import percent_format
import pandas as pd

from prepare_times_nz.utilities.filepaths import STAGE_1_DATA, STAGE_2_DATA, ANALYSIS
from prepare_times_nz.utilities.logger_setup import logger


OUTPUT_LOCATION = ANALYSIS / "results/load_curves"
OUTPUT_LOCATION.mkdir(parents = True, exist_ok= True)

LOAD_CURVE_DATA = STAGE_2_DATA / "settings/load_curves"

TOTAL_CONSUMPTION = 39135 # for reference 
BASE_YEAR = 2023 

base_year_load_curve = pd.read_csv(LOAD_CURVE_DATA / "base_year_load_curve.csv")
res_curves = pd.read_csv(LOAD_CURVE_DATA / "residential_curves.csv")
yrfr = pd.read_csv(LOAD_CURVE_DATA / "yrfr.csv")
eeud = pd.read_csv(STAGE_1_DATA / "eeud/eeud.csv")



eeud_elc = eeud[eeud["Fuel"] == "Electricity"]
eeud_elc = eeud_elc.groupby(["Year", "SectorGroup"])["Value"].sum().reset_index()
eeud_elc["GWH"] = (eeud_elc["Value"] / 3.6)

res_total_by = eeud_elc[eeud_elc["SectorGroup"] == "Residential"]
res_total_by = res_total_by[res_total_by["Year"] == BASE_YEAR]

res_curves["TotalDemand"] = res_total_by["GWH"].iloc[0]

res_curves["GWh"] = res_curves["TotalDemand"] * res_curves["LoadCurve"]

res_curves = res_curves.merge(yrfr)
res_curves["HoursInSlice"] = res_curves["YRFR"] * 365 * 24
res_curves["AverageLoadGW"] = res_curves["GWh"] / res_curves["HoursInSlice"]



base_year_load_curve["TEST"] = base_year_load_curve["LoadCurve"].sum()
base_year_load_curve["TEST2"] = base_year_load_curve["Value"].sum()

print(res_curves)

# 1) Split and order
df = res_curves.copy()
df[['Season','Daytype','TOD']] = df['TimeSlice'].str.split('-', expand=True)

season_order = ['WIN','SPR','SUM','FAL']
day_order    = ['WK','WE']
tod_order    = ['P','D','N']

codes_order = ['-'.join([s,d,t]) for s,d,t in product(season_order, day_order, tod_order)]
df['TimeSlice'] = pd.Categorical(df['TimeSlice'], categories=codes_order, ordered=True)


df['Season']  = pd.Categorical(df['Season'], categories=season_order, ordered=True)
df['Daytype'] = pd.Categorical(df['Daytype'], categories=day_order, ordered=True)
df['TOD']     = pd.Categorical(df['TOD'], categories=tod_order, ordered=True)

# 2) Human-readable nested labels
season_lbl = {'WIN':'Winter','SPR':'Spring','SUM':'Summer','FAL':'Fall'}
day_lbl    = {'WK':'Weekday','WE':'Weekend'}
tod_lbl    = {'P':'Peak','D':'Day','N':'Night'}
label_map  = {c: f"{season_lbl[s]}\n{day_lbl[d]}\n{tod_lbl[t]}"
              for s,d,t in product(season_order, day_order, tod_order)
              for c in ['-'.join([s,d,t])]}




season_lbl = {'WIN':'Winter','SPR':'Spring','SUM':'Summer','FAL':'Fall'}
day_lbl    = {'WK':'Weekday','WE':'Weekend'}
lab_season = lambda s: season_lbl.get(s, s)
lab_day    = lambda d: day_lbl.get(d, d)
season_colors = {
    'WIN': '#56B4E9',   # light blue
    'SUM': '#E69F00',   # dark orange
    'SPR': '#009E73',   # greenish
    'FAL': '#D55E00',   # reddish/orange
}

chart = (
    ggplot(df, aes(x='TOD', y='AverageLoadGW', fill = "Season"))
    + geom_col()
    + coord_flip()
    + facet_grid('Season ~ Daytype', labeller=labeller(Season=lab_season, Daytype=lab_day))
    + scale_x_discrete(labels={'P':'Peak','D':'Day','N':'Night'})
    + theme_classic()
    + labs(title = "Average residential load by timeslice", y = "GW", x = "", fill = "")
    + scale_fill_manual(values=season_colors)
    + scale_y_continuous(limits = [0,3])
    + theme(legend_position = "none")
)
chart.save(OUTPUT_LOCATION / "residential_load_curves.png", dpi = 300, height = 5, width = 8)
    
"""
"""

