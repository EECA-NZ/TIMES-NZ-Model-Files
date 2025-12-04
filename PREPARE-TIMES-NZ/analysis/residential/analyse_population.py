"""quick analysis of population projections"""

import pandas as pd

# pylint: disable = unused-import, unused-wildcard-import, wildcard-import
from plotnine import *
from prepare_times_nz.utilities.filepaths import ANALYSIS, STAGE_1_DATA

# all we want right now is to get a chart of the current + projected population

CURRENT_POP_FILE = STAGE_1_DATA / "statsnz/estimated_resident_population.csv"
PROJECTED_POP_FILE = STAGE_1_DATA / "statsnz/projections_national_2024.csv"

OUTPUT_LOCATION = ANALYSIS / "results/population_projections"
OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)

MAX_YEAR = 2050


df = pd.read_csv(CURRENT_POP_FILE)
df = df[df["Area"] == "New Zealand"]
df["Scenario"] = "Historical"
df["Variable"] = "ERP 2024-base"


EECA_TEAL = "#447474"
EECA_CORAL = "#ED6D63"
colours = [EECA_CORAL, EECA_TEAL]


df_current = df.copy()

df = pd.read_csv(PROJECTED_POP_FILE)
df["Area"] = "New Zealand"

# df = df[df["Year"] != 2024] # remove projection of historical year
df_projected = df.copy()

df = pd.concat([df_current, df_projected])

# make value millions

df["Value"] = df["Value"] / 1e6

# filter some scenarios
scenarios = [
    "Historical",
    # '5th percentile',
    "50th percentile (median)",
    # '95th percentile'
]
df = df[df["Scenario"].isin(scenarios)]

# filter max year

df = df[df["Year"] <= MAX_YEAR]

df["ValueLabel"] = df["Value"].round(2).astype(str) + "m"
df["YearAdjust"] = df["Year"] - 2

# latest_year

# chart
chart = (
    ggplot(df, aes(y="Value", x="Year"))
    + geom_line(aes(colour="Scenario"), size=1)
    + geom_label(
        aes(x="YearAdjust", label="ValueLabel"),
        colour="white",
        fill=EECA_CORAL,
        data=df[df["Year"] == MAX_YEAR],
    )
    # + facet_wrap("~DwellingType", scales = "free_x")
    # + coord_flip()
    + scale_colour_manual(values=colours, na_value="black")
    + scale_y_continuous(limits=[0, 8])
    + labs(
        x="Year",
        y="Population (millions)",
        colour="Scenario",
        title="Residential growth projections",
    )
    + theme_minimal()
)


CHART_NAME = "population_projections.png"
chart.save(OUTPUT_LOCATION / CHART_NAME, dpi=300, height=4, width=8)
