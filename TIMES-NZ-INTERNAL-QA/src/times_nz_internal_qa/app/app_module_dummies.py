"""
App processing for dummy processes
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

## Quite messy input data processing

dummy_energy_raw = pd.read_parquet(FINAL_DATA / "dummy_energy.parquet")
dummy_demand_raw = pd.read_parquet(FINAL_DATA / "dummy_demand.parquet")


# CONSTANTS ---------------------------------------


dummy_energy_group_options = ["Fuel", "Commodity", "Region"]
dummy_demand_group_options = [
    "SectorGroup",
    "Sector",
    "EndUse",
    "Commodity",
    "Region",
]


# define filter options. see create_filter_dict for details
dummy_demand_filters = create_filter_dict(
    "dummy_demand",  # chart id for all of these
    # list of dicts
    [
        {"col": "SectorGroup", "label": "Sector Group"},
        {"col": "Sector"},
        {"col": "EndUse", "label": "End use"},
        {"col": "Commodity"},
        {"col": "Region"},
    ],
)

dummy_energy_filters = create_filter_dict(
    "dummy_energy",
    [
        {"col": "Fuel"},
        {"col": "Region"},
        {"col": "Commodity"},
    ],
)

# SERVER ------------------------------------------------------------------


# pylint:disable = unused-argument
def dummy_server(inputs, outputs, session):
    """
    Server functions for dummy process module
    """

    # GET MAIN DATA
    def get_df_dummy(df_r):
        df = df_r[df_r["Scenario"] == "traditional-v3_0_0"].copy()
        df["Period"] = df["Period"].astype("Int64")
        return df

    df_dummy_demand = get_df_dummy(dummy_demand_raw)
    df_dummy_energy = get_df_dummy(dummy_energy_raw)

    # REGISTER ALL FILTER FUNCTIONS FOR UI
    for fs in dummy_demand_filters:
        register_filter_from_factory(
            fs, df_dummy_demand, dummy_demand_filters, inputs, outputs, session
        )

    for fs in dummy_energy_filters:
        register_filter_from_factory(
            fs, df_dummy_energy, dummy_energy_filters, inputs, outputs, session
        )

    # APPLY FILTERS TO DATA DYNAMICALLY
    @reactive.calc
    def df_dummy_demand_filtered():
        d = df_dummy_demand.copy()
        return apply_filters(d, dummy_demand_filters, inputs)

    @reactive.calc
    def df_dummy_energy_filtered():
        d = df_dummy_energy.copy()
        return apply_filters(d, dummy_energy_filters, inputs)

    # APPPLY DYNAMIC GROUPING AFTER FILTERING
    @reactive.calc
    def dummy_demand_grouped():
        d = df_dummy_demand_filtered()
        return (
            d.groupby(["Scenario", "Period"] + [inputs.dummy_demand_group()])["Value"]
            .sum()
            .reset_index()
        )

    @reactive.calc
    def dummy_energy_grouped():
        d = df_dummy_energy_filtered()
        return (
            d.groupby(["Scenario", "Period"] + [inputs.dummy_energy_group()])["Value"]
            .sum()
            .reset_index()
        )

    # RENDER CHARTS
    @outputs(id="dummy_demand_chart")
    @render_altair
    def _():
        d = dummy_demand_grouped()
        dc = complete_periods(
            d,
            period_list=range(2023, 2051),
            # base cols but not period
            category_cols=["Scenario"],
        )

        return (
            alt.Chart(dc)
            .mark_bar(size=50, opacity=0.85)
            .encode(
                x=alt.X("Period:N", title="Year"),
                y=alt.Y("Value:Q", title="PJ"),
                color=f"{inputs.dummy_demand_group()}:N",
                tooltip=[
                    # alt.Tooltip("PlantName:N", title=""),
                    alt.Tooltip(
                        f"{inputs.dummy_demand_group()}:N",
                        title=inputs.dummy_demand_group(),
                    ),
                    alt.Tooltip("Value:Q", title="PJ", format=",.2f"),
                    # alt.Tooltip("y:Q", title="Y", format=",.2f"),
                ],
            )
        )

    @outputs(id="dummy_energy_chart")
    @render_altair
    def _():
        d = dummy_energy_grouped()
        dc = complete_periods(
            d,
            period_list=range(2023, 2051),
            # base cols but not period
            category_cols=["Scenario"],
        )

        return (
            alt.Chart(dc)
            .mark_bar(size=50, opacity=0.85)
            .encode(
                x=alt.X("Period:N", title="Year"),
                y=alt.Y("Value:Q", title="PJ"),
                color=f"{inputs.dummy_energy_group()}:N",
                tooltip=[
                    # alt.Tooltip("PlantName:N", title=""),
                    alt.Tooltip(
                        f"{inputs.dummy_energy_group()}:N",
                        title=f"{inputs.dummy_energy_group()}",
                    ),
                    alt.Tooltip("Value:Q", title="PJ", format=",.2f"),
                    # alt.Tooltip("y:Q", title="Y", format=",.2f"),
                ],
            )
        )

    # DOWNLOADS

    @render.download(filename="df_dummy_demand.csv", media_type="text/csv")
    def dummy_demand_chart_data_download():
        buf = io.StringIO()
        df_dummy_demand.to_csv(buf, index=False)
        yield buf.getvalue()

    @render.download(filename="df_dummy_energy.csv", media_type="text/csv")
    def dummy_energy_chart_data_download():
        buf = io.StringIO()
        df_dummy_energy.to_csv(buf, index=False)
        yield buf.getvalue()


# UI --------------------------------------------------


# pylint:disable = too-many-positional-arguments, too-many-arguments, duplicate-code
# should move this to a ui helper module
def section_block(sec_id, title, group_input_id, group_options, filters, chart_id):
    """
    Defines the ui layout of an individual chart. Flexible input params
    """
    return ui.div(
        ui.layout_columns(
            ui.tags.h3(title, id=sec_id),
            ui.input_select(group_input_id, "Group by:", group_options),
            ui.download_button(
                f"{chart_id}_data_download", f"Download all {title.lower()}"
            ),
        ),
        ui.span("Filters"),
        ui.div(*filter_output_ui_list(filters), class_="dummy-filters"),
        output_widget(chart_id),
        class_="dummy-section",
    )


sections = [
    (
        "dummy-demand",
        "Infeasible demand",
        "dummy_demand_group",
        dummy_demand_group_options,
        dummy_demand_filters,
        "dummy_demand_chart",
    ),
    (
        "dummy-energy",
        "Infeasible energy",
        "dummy_energy_group",
        dummy_energy_group_options,
        dummy_energy_filters,
        "dummy_energy_chart",
    ),
]


toc = ui.div(
    *[ui.tags.a(lbl, href=f"#{sid}", class_="toc-link") for sid, lbl, *_ in sections],
    id="dummy-toc",
)

content = ui.div(
    *[section_block(*s) for s in sections],
    id="dummy-content",
)
dummy_ui = ui.page_fluid(
    ui.tags.style(
        """
    #dummy-layout{display:flex; gap:16px;}
    #dummy-toc{width:240px; flex:0 0 240px; position:sticky; top:0; align-self:flex-start; 
              max-height:calc(100vh - 120px); overflow:auto; border-right:1px solid #eee;
              padding-right:12px;}     
    #dummy-content{flex:1 1 auto; max-height:calc(100vh - 120px); overflow:auto;
                padding-right:12px;}
    .dummy-filters{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
                     gap:12px;}
    .toc-link{display:block; padding:6px 0; text-decoration:none;}
    .dummy-section h3{scroll-margin-top:12px;}
    """
    ),
    # combine the generated toc and content
    ui.div(toc, content, id="dummy-layout"),
    # javascript for in-pane scrolling
    ui.tags.script(
        """
    (function(){
      const scroller = document.getElementById('dummy-content');
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
