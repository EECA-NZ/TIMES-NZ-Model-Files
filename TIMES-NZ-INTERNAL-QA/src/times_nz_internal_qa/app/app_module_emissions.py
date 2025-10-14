"""
Data formatting, server and ui functions for emissions data

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

# define base columns that we must always group by
base_cols = [
    "Scenario",
    "Period",
    "Unit",
]

# define filter options with optional labels
ems_filters_raw = [
    {"col": "SectorGroup", "label": "Sector Group"},
    {"col": "Sector"},
    {"col": "TechnologyGroup", "label": "Technology Group"},
    {"col": "Technology"},
    {"col": "EnduseGroup"},
    {"col": "EndUse"},
    {"col": "Region"},
    {"col": "Process"},
    {"col": "PlantName"},
]
# build filter dict
ems_filters = create_filter_dict("emissions", ems_filters_raw)
# base group options on defined filter options
ems_group_options = [d["col"] for d in ems_filters_raw]


# DATA PROCESSING
def get_emissions_df():
    """
    Formatting for emissions. Very minor handling
    """

    df = pd.read_parquet(FINAL_DATA / "emissions.parquet")
    df["Period"] = df["Period"].astype(int)

    df = df.fillna("-")
    df = df[df["Scenario"] == "traditional-v3_0_0"]
    return df


# pylint:disable = too-many-locals, unused-argument
def emissions_server(inputs, outputs, session):
    """
    server functions for electricity
    """

    # data
    emissions_df = get_emissions_df()

    # Register all filters
    for fs in ems_filters:
        register_filter_from_factory(
            fs, emissions_df, ems_filters, inputs, outputs, session
        )

    # dynamically filter data

    @reactive.calc
    def emissions_df_filtered():
        d = emissions_df.copy()
        d = apply_filters(d, ems_filters, inputs)
        return d.groupby(base_cols + [inputs.ems_group()])["Value"].sum().reset_index()

    # CHART
    @outputs(id="ems_chart")
    @render_altair
    def _():
        df = emissions_df_filtered()
        unit = df["Unit"].unique()[0]
        group_col = inputs.ems_group()
        dc = complete_periods(
            df,
            period_list=range(2023, 2051),
            # group by everything important except period
            category_cols=[c for c in base_cols if c != "Period"] + [group_col],
        )

        return (
            # pylint: disable = duplicate-code
            alt.Chart(dc)
            .mark_bar(size=40, opacity=0.85)
            .encode(
                x=alt.X("Period:N", title="Year"),
                y=alt.Y("Value:Q", title=f"{unit}"),
                color=f"{group_col}:N",
                tooltip=[
                    alt.Tooltip(f"{group_col}:N", title=group_col),
                    alt.Tooltip("Value:Q", title=f"{unit}", format=",.2f"),
                ],
            )
        )

    # DOWNLOADS
    # Generate download
    @render.download(filename="ems_chart_data_download.csv", media_type="text/csv")
    def ems_chart_data_download():
        buf = io.StringIO()
        emissions_df_filtered().to_csv(buf, index=False)
        yield buf.getvalue()

    @render.download(filename="ems_data_raw.csv", media_type="text/csv")
    def ems_all_data_download():
        buf = io.StringIO()
        emissions_df.to_csv(buf, index=False)
        yield buf.getvalue()


# UI ---------------------------------------------------------------


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
        ui.div(*filter_output_ui_list(filters), class_="ems-filters"),
        output_widget(chart_id),
        class_="ems-section",
    )


sections = [
    (
        "ems-total",
        "Energy emissions",
        "ems_group",
        ems_group_options,
        ems_filters,
        "ems_chart",
    )
]

toc = ui.div(
    *[ui.tags.a(lbl, href=f"#{sid}", class_="toc-link") for sid, lbl, *_ in sections],
    id="ems-toc",
)

content = ui.div(
    *[section_block(*s) for s in sections],
    id="ems-content",
)
emissions_ui = ui.page_fluid(
    ui.tags.style(
        """
    #ems-layout{display:flex; gap:16px;}
    #ems-toc{width:240px; flex:0 0 240px; position:sticky; top:0; align-self:flex-start; 
              max-height:calc(100vh - 120px); overflow:auto; 
              border-right:1px solid #eee; padding-right:12px;}     
    #ems-content{flex:1 1 auto; max-height:calc(100vh - 120px); 
              overflow:auto; padding-right:12px;}
    .ems-filters{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
                 gap:12px;}
    .toc-link{display:block; padding:6px 0; text-decoration:none;}
    .ems-section h3{scroll-margin-top:12px;}
    """
    ),
    # combine the generated toc and content
    ui.download_button("ems_all_data_download", "Download raw data"),
    ui.div(toc, content, id="ems-layout"),
    # javascript for in-pane scrolling
    ui.tags.script(
        """
    (function(){
      const scroller = document.getElementById('ems-content');
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
