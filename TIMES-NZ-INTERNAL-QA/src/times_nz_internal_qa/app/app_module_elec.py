"""
Data formatting, server and ui functions for electricity generation data

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

# CONSTANTS  ------------------------------------------------------------------------------
# define base columns that we must always group by
ele_base_cols = [
    "Scenario",
    "Variable",
    "Period",
    "Unit",
]

# parameters to optionally group data by
# Note: we can add Fuel for the fuel inputs
ele_core_group_options = [
    "TechnologyGroup",
    "Technology",
    "Region",
    "PlantName",
]

# configure filter options
core_filters = [
    {"col": "TechnologyGroup", "label": "Technology Group"},
    {"col": "Technology"},
    {"col": "Region"},
    {"col": "PlantName", "label": "Plant"},
]

fuel_filters = [
    {"col": "Fuel"},
]

ele_gen_filters = create_filter_dict("ele_gen", core_filters)
ele_cap_filters = create_filter_dict("ele_cap", core_filters)
ele_use_filters = create_filter_dict("ele_use", core_filters + fuel_filters)

# PROCESS DATA


def get_base_ele_df():
    """Minor tidting of the base input"""

    df = pd.read_parquet(FINAL_DATA / "elec_generation.parquet")
    df = df.fillna("-")
    df["Period"] = df["Period"].astype(int)
    df = df[df["Scenario"] == "traditional-v3_0_0"]  # placeholder

    return df


def get_ele_gen_data(df, variable):
    """
    Filter for the variable we want to display
    Convert PJ to GWh for output
    """
    df = df[df["Variable"] == variable].copy()
    if variable == "Electricity generation":
        df["Value"] = df["Value"] * 277.78
        df["Unit"] = "GWh"
    return df


# Process data
base_df = get_base_ele_df()
ele_gen_df = get_ele_gen_data(base_df, "Electricity generation")
ele_cap_df = get_ele_gen_data(base_df, "Electricity generation capacity")
ele_use_df = get_ele_gen_data(base_df, "Electricity fuel use")


# pylint:disable = too-many-locals, unused-argument
def elec_server(inputs, outputs, session):
    """
    server functions for electricity
    """

    # REGISTER ALL FILTER FUNCTIONS FOR UI
    # Currently we do this once per chart
    for fs in ele_gen_filters:
        register_filter_from_factory(
            fs, ele_gen_df, ele_gen_filters, inputs, outputs, session
        )

    for fs in ele_cap_filters:
        register_filter_from_factory(
            fs, ele_cap_df, ele_cap_filters, inputs, outputs, session
        )

    for fs in ele_use_filters:
        register_filter_from_factory(
            fs, ele_use_df, ele_use_filters, inputs, outputs, session
        )

    # APPLY FILTERS TO DATA DYNAMICALLY (group afterwards)
    @reactive.calc
    def ele_cap_df_filtered():
        d = ele_cap_df.copy()
        d = apply_filters(d, ele_cap_filters, inputs)
        return (
            d.groupby(ele_base_cols + [inputs.ele_cap_group()])["Value"]
            .sum()
            .reset_index()
        )

    @reactive.calc
    def ele_use_df_filtered():
        d = ele_use_df.copy()
        d = apply_filters(d, ele_use_filters, inputs)
        return (
            d.groupby(ele_base_cols + [inputs.ele_use_group()])["Value"]
            .sum()
            .reset_index()
        )

    @reactive.calc
    def ele_gen_df_filtered():
        d = ele_gen_df.copy()
        d = apply_filters(d, ele_gen_filters, inputs)
        return (
            d.groupby(ele_base_cols + [inputs.ele_gen_group()])["Value"]
            .sum()
            .reset_index()
        )

    # CHARTS

    # we make this once then pass parameters to build each one

    def build_grouped_bar(df, base_cols, group_col, period_range=range(2023, 2051)):
        dc = complete_periods(
            df,
            period_list=period_range,
            category_cols=[c for c in base_cols if c != "Period"] + [group_col],
        )
        # unit defined in the data itself
        # side benefit that we can see if any units are inconsistent within a chart
        unit = dc["Unit"].unique().tolist()
        return (
            alt.Chart(dc)
            .mark_bar(size=40, opacity=0.85)
            .encode(
                x=alt.X("Period:N", title="Year"),
                y=alt.Y("Value:Q", title=unit),
                color=f"{group_col}:N",
                tooltip=[
                    alt.Tooltip(f"{group_col}:N", title=group_col),
                    alt.Tooltip("Value:Q", title=unit, format=",.2f"),
                ],
            )
        )

    # build the 3 charts
    @outputs(id="ele_gen_chart")
    @render_altair
    def _():
        return build_grouped_bar(
            ele_gen_df_filtered(), ele_base_cols, inputs.ele_gen_group()
        )

    @outputs(id="ele_use_chart")
    @render_altair
    def _():
        return build_grouped_bar(
            ele_use_df_filtered(), ele_base_cols, inputs.ele_use_group()
        )

    @outputs(id="ele_cap_chart")
    @render_altair
    def _():
        return build_grouped_bar(
            ele_cap_df_filtered(), ele_base_cols, inputs.ele_cap_group()
        )

    # CSV downloads (not yet functionalised sorry)

    @render.download(filename="ele_gen_chart_data_download.csv", media_type="text/csv")
    def ele_gen_chart_data_download():
        buf = io.StringIO()
        ele_gen_df_filtered().to_csv(buf, index=False)
        yield buf.getvalue()

    @render.download(filename="ele_use_chart_data_download.csv", media_type="text/csv")
    def ele_use_chart_data_download():
        buf = io.StringIO()
        ele_use_df_filtered().to_csv(buf, index=False)
        yield buf.getvalue()

    @render.download(filename="ele_cap_chart_data_download.csv", media_type="text/csv")
    def ele_cap_chart_data_download():
        buf = io.StringIO()
        ele_cap_df_filtered().to_csv(buf, index=False)
        yield buf.getvalue()

    @render.download(filename="ele_gen_data_raw.csv", media_type="text/csv")
    def ele_all_data_download():
        buf = io.StringIO()
        base_df.to_csv(buf, index=False)
        yield buf.getvalue()


# UI ------------------------------------------------


# pylint:disable = too-many-positional-arguments, too-many-arguments, duplicate-code
# probably need to send this function to a helper and have each module import it
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
        ui.div(*filter_output_ui_list(filters), class_="elec-filters"),
        output_widget(chart_id),
        class_="elec-section",
    )


sections = [
    (
        "elec-gen",
        "Electricity generation",
        "ele_gen_group",
        ele_core_group_options,
        ele_gen_filters,
        "ele_gen_chart",
    ),
    (
        "elec-use",
        "Fuel used for generation",
        "ele_use_group",
        ele_core_group_options,
        ele_use_filters,
        "ele_use_chart",
    ),
    (
        "elec-cap",
        "Generation capacity",
        "ele_cap_group",
        ele_core_group_options,
        ele_cap_filters,
        "ele_cap_chart",
    ),
]

toc = ui.div(
    *[ui.tags.a(lbl, href=f"#{sid}", class_="toc-link") for sid, lbl, *_ in sections],
    id="elec-toc",
)

content = ui.div(
    *[section_block(*s) for s in sections],
    id="elec-content",
)

elec_ui = ui.page_fluid(
    ui.tags.style(
        """
    #elec-layout{display:flex; gap:16px;}
    #elec-toc{width:240px; flex:0 0 240px; position:sticky;
                    top:0; align-self:flex-start; 
                    max-height:calc(100vh - 120px);
                    overflow:auto; border-right:1px solid #eee; padding-right:12px;}     
    #elec-content{flex:1 1 auto; max-height:calc(100vh - 120px); 
                    overflow:auto; padding-right:12px;}
    .elec-filters{ display:grid;
                    grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
                    gap:12px;}
    .toc-link{display:block; padding:6px 0; text-decoration:none;}
    .elec-section h3{scroll-margin-top:12px;}
    """
    ),
    # combine the generated toc and content
    ui.download_button("ele_all_data_download", "Download raw data"),
    ui.div(toc, content, id="elec-layout"),
    # javascript for in-pane scrolling
    ui.tags.script(
        """
    (function(){
      const scroller = document.getElementById('elec-content');
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
