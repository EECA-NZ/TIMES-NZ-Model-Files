



from times_nz_internal_qa.utilities.filepaths import FINAL_DATA
import times_nz_internal_qa.analysis.get_data as chart_data
from times_nz_internal_qa.config import current_scenarios


from plotnine import (
    ggplot, aes, geom_line, geom_point, geom_text, geom_label, geom_area,
    scale_x_continuous, scale_y_continuous, theme, scale_fill_manual,
    scale_color_manual,
    labs, theme_minimal
)


from plotnine import (
    ggplot, aes, geom_line, geom_point, geom_text, geom_label, geom_area,
    scale_x_continuous, scale_y_continuous, theme, scale_fill_manual,
    scale_color_manual,
    labs, theme_minimal
)


eeca_colours = {
    "emerald": "#41B496",
    "teal": "#447474",
    "navy": "#164057",
    "coral": "#ED6D63",
    "forest": "#3C4C49",
    "orange" : "#E94E24",
}

chart_cols = [
    eeca_colours["navy"],
    eeca_colours["coral"],
    eeca_colours["teal"],
    eeca_colours["forest"],
    eeca_colours["emerald"],
    eeca_colours["orange"],
]



def process_heat_chart(df, scenario):
    """Create and save an area chart for industrial process heat demand."""

    df = df[df["Scenario"] == scenario].copy()
    if df.empty:
        raise ValueError(f"No process heat data found for scenario '{scenario}'.")

    df["Period"] = pd.to_numeric(df["Period"], errors="coerce")

    # keep a fixed fuel order so stacking/order is stable
    fuel_order = [
        "Biogas",
        "Biomass",
        "Coal",
        "Electricity",
        "Natural gas",
        "Other",
    ]
    df["Fuel"] = pd.Categorical(df["Fuel"], categories=fuel_order, ordered=True)

    # aggregate first, if needed
    df = (
        df.groupby(["Scenario", "Period", "Fuel"], as_index=False, observed=False)["Value"]
        .sum()
    )

    # complete all Period x Fuel combinations and fill missing with zero
    periods = sorted(df["Period"].dropna().unique())
    full_index = pd.MultiIndex.from_product(
        [[scenario], periods, fuel_order],
        names=["Scenario", "Period", "Fuel"]
    )

    df = (
        df.set_index(["Scenario", "Period", "Fuel"])
          .reindex(full_index, fill_value=0)
          .reset_index()
    )

    ph_cols = [
        eeca_colours["navy"],
        eeca_colours["teal"],
        eeca_colours["forest"],
        eeca_colours["emerald"],
        eeca_colours["orange"],
        "grey",
    ]

    p = (
        ggplot(df, aes(x="Period", y="Value", fill="Fuel", group="Fuel"))
        + geom_area()
        + labs(
            title="Industrial process heat demand",
            x="Year",
            y="PJ"
        )
        + scale_x_continuous(breaks=[2025, 2030, 2035, 2040, 2045, 2050])
        + scale_y_continuous(limits=(0, None), labels=comma_format())
        + scale_fill_manual(values=ph_cols, limits=fuel_order)
        + theme_minimal()
    )

    filename = scenario.lower().replace(" ", "_")
    p.save(f"analysis/industrial_process_heat_{filename}.png", dpi=300, height=4, width=5)






def make_chart(df, unit, chart_title):
    """Create and save a labelled scenario line chart for the supplied data."""

    scenario_order = df["Scenario"].drop_duplicates().tolist()
    palette = {
        scenario: chart_cols[i % len(chart_cols)]
        for i, scenario in enumerate(scenario_order)
    }
        
    df_last = (
    df.sort_values("Period")
      .groupby("Scenario", as_index=False)
      .tail(1)
    )

    df_last["label"] = df_last["Scenario"] + ": " + df_last["Value"].map(lambda v: f"{v:,.1f}") + " " + unit

    min_gap = 2

    df_last = df_last.sort_values("Value").copy()
    df_last["y_adjusted"] = df_last["Value"]

    for i in range(1, len(df_last)):
        prev = df_last.iloc[i - 1]["y_adjusted"]
        curr = df_last.iloc[i]["y_adjusted"]

        if curr - prev < min_gap:
            df_last.iloc[i, df_last.columns.get_loc("y_adjusted")] = prev + min_gap

    

        

    p = (
    ggplot(df, aes(x="Period", y="Value", color="Scenario"))
    + geom_line(size=1)    
     + geom_label(
        data=df_last,
        mapping=aes(x="Period", y="y_adjusted", label="label", fill="Scenario"),
        colour = "white",
        ha="left",
        
        nudge_x=0.5,
        size=8
    )
    + labs(
        title=chart_title,
        x="Year",
        y=unit
    )
              + scale_x_continuous(
                  breaks=[2025,2030,2035,2040,2045,2050],
                  limits = (2023, 2065)
     )
    + scale_y_continuous(limits=(0, None), labels=comma_format())
    + theme_minimal()
    + theme(legend_position = "none")
    + scale_color_manual(values=palette )
    + scale_fill_manual(values=palette )
    )

    p.save(f"analysis/{chart_title}.png",dpi = 300, height = 3, width = 4)




def chart_elec_gen(df): 
    """Create and save the electricity generation line chart."""


    df_last = (
    df.sort_values("Period")
      .groupby("Scenario", as_index=False)
      .tail(1)
    )

    df_last["label"] = df_last["Scenario"] + ": " + df_last["Value"].map(lambda v: f"{v:,.1f}") + "TWh"

        

    p = (
    ggplot(df, aes(x="Period", y="Value", color="Scenario"))
    + geom_line(size=1)    
     + geom_label(
        data=df_last,
        mapping=aes(x="Period", y="Value", label="label", fill="Scenario"),
        colour = "white",
        ha="left",
        
        nudge_x=0.5,
        size=8
    )
    + labs(
        title="Electricity generation",
        x="Year",
        y="TWh"
    )
              + scale_x_continuous(
breaks=[2025,2030,2035,2040,2045,2050],
limits = (2023, 2060)
     )
    + scale_y_continuous(limits=(0, None), labels=comma_format())
    + theme_minimal()
    + theme(legend_position = "none")
    + scale_color_manual(values=eeca_colours )
    + scale_fill_manual(values=eeca_colours )
    )

    p.save("analysis/elec.png",dpi = 300, height = 3, width = 4)



def main():
    """Build the analysis datasets and save the chart outputs."""

    df_elc = chart_data.get_elec_gen(compare_other_models = False)    
    df_ems = chart_data.get_emissions(compare_other_models = False)   

    df_pht = chart_data.get_process_heat()

    process_heat_chart(df_pht, "Steady")
    process_heat_chart(df_pht, "Shift")

    make_chart(df_elc, "TWh", "Electricity generation")
    make_chart(df_ems, "MT CO2e", "Energy emissions")

    


if __name__ == "__main__":
    main()
