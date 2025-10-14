"""
Energy demand processing, ui, and server functions
"""

import io

import altair as alt
import pandas as pd
from shiny import reactive, render, ui
from shinywidgets import output_widget, render_altair
from times_nz_internal_qa.app.filter_helpers import (
    apply_filters,
    create_filter_dict,
    filter_output_ui_list,
    register_filter_from_factory,
)
from times_nz_internal_qa.utilities.data_formatting import (
    complete_periods,
)
from times_nz_internal_qa.utilities.filepaths import FINAL_DATA

# CONSTANTS --------------------------------------------------


# SET FILTER/GROUP OPTIONS

dem_filters_raw = [
    {"col": "SectorGroup", "label": "Sector Group"},
    {"col": "Sector"},
    {"col": "TechnologyGroup", "label": "Technology Group"},
    {"col": "Technology"},
    {"col": "EnduseGroup"},
    {"col": "EndUse"},
    {"col": "Region"},
    {"col": "Fuel"},
    {"col": "Process"},
]

dem_filters = create_filter_dict("energy_dem", dem_filters_raw)
dem_group_options = [d["col"] for d in dem_filters_raw]

# Core variables we always group by

base_cols = [
    "Scenario",
    "Variable",
    "Period",
    "Unit",
]

# GET DATA ------------------------------------------


def get_energy_dem():
    """
    Formatting for all energy demand. Outputs the main data ready for web ingestion
    """

    df = pd.read_parquet(FINAL_DATA / "energy_demand.parquet")
    df = df.fillna("-")
    df = df[df["Scenario"] == "traditional-v3_0_0"]
    df["Period"] = df["Period"].astype("Int64")
    return df


# SERVER ------------------------------------------


# pylint:disable = too-many-locals, unused-argument, too-many-statements
def demand_server(inputs, outputs, session):
    """
    Server functions for energy demand module
    """
    energy_dem_df = get_energy_dem()

    # REGISTER ALL FILTER FUNCTIONS FOR UI
    for fs in dem_filters:
        register_filter_from_factory(
            fs, energy_dem_df, dem_filters, inputs, outputs, session
        )

    # DYNAMICALLY FILTER/GROUP DATA

    @reactive.calc
    def energy_dem_df_filtered():
        d = energy_dem_df.copy()
        d = apply_filters(d, dem_filters, inputs)
        return d.groupby(base_cols + [inputs.dem_group()])["Value"].sum().reset_index()

    # Render chart
    @outputs(id="dem_chart")
    @render_altair
    def _():
        group_col = inputs.dem_group()
        df = energy_dem_df_filtered()
        dc = complete_periods(
            df,
            period_list=range(2023, 2051),
            # group by everything important except period
            category_cols=[c for c in base_cols if c != "Period"] + [group_col],
        )

        return (
            alt.Chart(dc)
            .mark_bar(size=40, opacity=0.85)
            .encode(
                x=alt.X("Period:N", title="Year"),
                y=alt.Y("Value:Q", title="PJ"),
                color=f"{inputs.dem_group()}:N",
                tooltip=[
                    # alt.Tooltip("PlantName:N", title=""),
                    alt.Tooltip(f"{inputs.dem_group()}:N", title=inputs.dem_group()),
                    alt.Tooltip("Value:Q", title="PJ", format=",.2f"),
                    # alt.Tooltip("y:Q", title="Y", format=",.2f"),
                ],
            )
        )

    # Generate downloads
    @render.download(filename="dem_chart_data_download.csv", media_type="text/csv")
    def dem_chart_data_download():
        buf = io.StringIO()
        energy_dem_df_filtered().to_csv(buf, index=False)
        yield buf.getvalue()

    @render.download(filename="dem_data_raw.csv", media_type="text/csv")
    def dem_all_data_download():
        buf = io.StringIO()
        energy_dem_df.to_csv(buf, index=False)
        yield buf.getvalue()


# UI --------------------------------------------


# pylint:disable = too-many-positional-arguments, too-many-arguments
def section_block(sec_id, title, group_input_id, group_options, filters, chart_id):
    """
    Defines the ui layout of an individual chart. Flexible input params
    """
    return ui.div(
        ui.layout_columns(
            ui.tags.h3(title, id=sec_id),
            ui.input_select(group_input_id, "Group by:", group_options),
            ui.download_button(f"{chart_id}_data_download", "Download chart data"),
        ),
        ui.span("Filters"),
        ui.div(*filter_output_ui_list(filters), class_="dem-filters"),
        output_widget(chart_id),
        class_="dem-section",
    )


sections = [
    # single section for a single chart. Used
    (
        "dem-total",
        "Total energy demand",
        "dem_group",
        dem_group_options,
        dem_filters,
        "dem_chart",
    )
]

toc = ui.div(
    *[ui.tags.a(lbl, href=f"#{sid}", class_="toc-link") for sid, lbl, *_ in sections],
    id="dem-toc",
)

content = ui.div(
    *[section_block(*s) for s in sections],
    id="dem-content",
)

demand_ui = ui.page_fluid(
    ui.tags.style(
        """
    #dem-layout{display:flex; gap:16px;}
    #dem-toc{width:240px;    
              flex:0 0 240px;
              position:sticky;
              top:0;
              align-self:flex-start; 
              max-height:calc(100vh - 120px); 
              overflow:auto;
              border-right:1px solid #eee;
              padding-right:12px;}     
    #dem-content{flex:1 1 auto; 
            max-height:calc(100vh - 120px);
            overflow:auto; padding-right:12px;}
    .dem-filters{ display:grid; 
                grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
                gap:12px;}
    .toc-link{display:block; padding:6px 0; text-decoration:none;}
    .dem-section h3{scroll-margin-top:12px;}
    """
    ),
    # combine the generated toc and content
    ui.download_button("dem_all_data_download", "Download raw data"),
    ui.div(toc, content, id="dem-layout"),
    # javascript for in-pane scrolling
    ui.tags.script(
        """
    (function(){
      const scroller = document.getElementById('dem-content');
      document.addEventListener('click', function(e){
        const a = e.target.closest('a.toc-link');
        if(!a) return;
        e.preventDefault();
        const target = document.querySelector(a.getAttribute('href'));
        if(!target || !scroller) return;
        const y = target.offsetTop - scroller.offsetTop - 8;
        scroller.scrollTo({top: y, behavior: 'smooth'});
      }, true);
    })();
    """
    ),
)
