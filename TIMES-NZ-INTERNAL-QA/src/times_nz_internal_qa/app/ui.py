"""
Defines the ui for the internal app
"""

# Libraries
from shiny import ui

# from times_nz_internal_qa.app.app_module_demand import demand_ui
# from times_nz_internal_qa.app.app_module_dummies import dummy_ui
from times_nz_internal_qa.app.app_module_elec import elec_ui

# from times_nz_internal_qa.app.app_module_emissions import emissions_ui
from times_nz_internal_qa.app.helpers.ui_elements import tab_title
from times_nz_internal_qa.utilities.filepaths import ASSETS

# Constants

global_css = ASSETS / "styles.css"

# UI

app_ui = ui.page_fluid(
    ui.head_content(ui.include_css(global_css)),
    ui.tags.link(
        rel="stylesheet",
        href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css",
    ),
    # HEADER PANEL
    ui.div(
        # top line
        ui.div(
            ui.h1("TIMES-NZ 3.0 Explorer: Internal QA"),
            ui.h1("NOT FOR RELEASE - WIP", style="color:red; font-weight:bold;"),
            style="display:flex; align-items:center; justify-content:space-between;",
        ),
        # bottom line
        ui.div(
            # left section (scenario controls)
            ui.div(
                ui.input_switch("compare_on", "Compare scenarios"),
                ui.output_ui("select_scenario_a_ui"),
                ui.output_ui("select_scenario_b_ui"),
                style="display:flex; align-items:center; gap:10px;",
            ),
            # right section (info buttons)
            ui.div(
                ui.input_action_button(
                    "info_btn_101",
                    ui.tags.span(
                        ui.tags.i(
                            class_="fa fa-circle-info", style="margin-right:6px;"
                        ),
                        "TIMES-NZ 101",
                    ),
                    class_="header-info-btn",
                    title="TIMES-NZ 101",
                ),
                ui.input_action_button(
                    "info_btn_use",
                    ui.tags.span(
                        ui.tags.i(
                            class_="fa fa-circle-info", style="margin-right:6px;"
                        ),
                        "Using this app",
                    ),
                    class_="header-info-btn",
                    title="Using this app",
                ),
                style=(
                    "display:flex;"
                    "flex-direction:column;"
                    "align-items:flex-end; gap:6px;"
                ),
            ),
            style=(
                "display:flex;"
                "align-items:center;"
                "justify-content:space-between;"
                "margin-top:8px;"
            ),
        ),
        style="padding:10px 20px; border-bottom:1px solid #ccc;",
    ),
    # EXPLORER NAVSET PAGES
    ui.div(
        ui.navset_tab(
            ui.nav_panel(tab_title("Electricity generation", "info_elc"), elec_ui),
            # ui.nav_panel(tab_title("Energy demand", "info_dem"), demand_ui),
            # ui.nav_panel(
            #     tab_title("Infeasibilities", "info_dum"),
            #     dummy_ui,
            # ),
            # ui.nav_panel(tab_title("Emissions", "info_ems"), emissions_ui),
        ),
        class_="navset-large",
    ),
)
