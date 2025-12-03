"""
Defines the ui for the internal app
"""

# Libraries
from shiny import ui
from times_nz_internal_qa.app.app_module_demand import demand_ui
from times_nz_internal_qa.app.app_module_elec import elec_ui
from times_nz_internal_qa.app.app_module_emissions import emissions_ui
from times_nz_internal_qa.app.app_module_esd import esd_ui
from times_nz_internal_qa.app.app_module_primary_energy import primary_energy_ui
from times_nz_internal_qa.app.helpers.ui_elements import tab_title
from times_nz_internal_qa.utilities.filepaths import ASSETS

# Constants

global_css = ASSETS / "styles.css"

# UI

app_ui = ui.page_fluid(

    ui.head_content(
        # Google Fonts
        ui.tags.link(rel="preconnect", href="https://fonts.googleapis.com"),
        ui.tags.link(
            rel="preconnect",
            href="https://fonts.gstatic.com",
            crossorigin="anonymous",
        ),
        ui.tags.link(
            rel="stylesheet",
            href=(
                "https://fonts.googleapis.com/css2?"
                "family=Roboto:ital,wght@0,100..900;1,100..900&display=swap"
            ),
        ),

        # Font Awesome
        ui.tags.link(
            rel="stylesheet",
            href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css",
        ),

        # Your global CSS (last so it can override everything)
        ui.include_css(global_css),
    ),
    
    # HEADER PANEL
    ui.div(
        # top line
        # ui.div(
        #    ui.h1("TIMES-NZ 3.0 Explorer: Internal QA"),
        #    ui.h1("NOT FOR RELEASE - WIP", style="color:red; font-weight:bold;"),
        #    style="display:flex; align-items:center; justify-content:space-between;",
        # ),
        # bottom line
        ui.div(
            # left section (scenario controls)
            ui.div(
                ui.output_ui("select_scenario_a_ui"),
                ui.input_switch("compare_on", "Compare with..."),
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
        #style="padding:10px 20px; border-bottom:1px solid #ccc;",
    ),
    # EXPLORER NAVSET PAGES
    ui.div(
        ui.navset_tab(
            ui.nav_panel(tab_title("Primary energy", "info_pri"), primary_energy_ui),
            ui.nav_panel(tab_title("Energy demand", "info_dem"), demand_ui),
            ui.nav_panel(tab_title("Electricity generation", "info_elc"), elec_ui),
            ui.nav_panel(tab_title("Emissions", "info_ems"), emissions_ui),
            ui.nav_panel(tab_title("Energy service demand", "info_esd"), esd_ui),
            # ui.nav_panel(tab_title("Infeasibilities", "info_dum"), dummy_ui),
        ),
        class_="navset-large",
    ),
)
