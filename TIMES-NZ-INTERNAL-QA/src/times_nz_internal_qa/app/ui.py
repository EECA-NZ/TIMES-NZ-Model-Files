"""
Defines the ui for the internal app
"""

import json
import os
from pathlib import Path

# Libraries
from dotenv import load_dotenv
from shiny import ui
from times_nz_internal_qa.app.app_module_demand import demand_ui
from times_nz_internal_qa.app.app_module_dummies import dummy_ui
from times_nz_internal_qa.app.app_module_elec import elec_ui
from times_nz_internal_qa.app.app_module_emissions import emissions_ui
from times_nz_internal_qa.app.app_module_esd import esd_ui
from times_nz_internal_qa.app.app_module_primary_energy import primary_energy_ui
from times_nz_internal_qa.utilities.filepaths import ASSETS

# Constants

global_css = ASSETS / "styles.css"

# Secrets

load_dotenv(dotenv_path=Path.cwd() / ".env")
PENDO_API_KEY = os.getenv("PENDO_API_KEY", "")

# UI

app_ui = ui.page_fluid(
    ui.head_content(
        ui.tags.title("TIMES-NZ 3.0 Explorer"),
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
        # IFrame resizer
        ui.tags.script(
            src="https://cdn.jsdelivr.net/npm/@iframe-resizer/child@latest",
            type="text/javascript",
        ),
        # Pendo
        ui.tags.script(
            f"window.PENDO_API_KEY = {json.dumps(PENDO_API_KEY)};",
            type="text/javascript",
        ),
        ui.tags.script(
            src="js/pendo-analytics.js",
            type="text/javascript",
        ),
        # Selectizer auto-position dropdowns
        ui.tags.script(
            src="js/auto-position.js",
            type="text/javascript",
        ),
        ui.tags.script(
            src="js/chart-toggle-width.js",
            type="text/javascript",
        ),
        ui.tags.script(
            src="js/custom-plotly-hover.js",
            type="text/javascript",
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
                ui.div(
                    ui.tags.h4("Comparison scenario (optional):", class_="filter-section-title"),
                    ui.input_selectize(
                        "scenario_b",
                        label=None,
                        choices={"__none__": "None"},
                        selected="__none__",
                        options={"plugins": ["auto_position"]},
                    ),
                    class_="scenario-selector-field",
                ),
                style="display:flex; align-items:flex-end; gap:10px;",
                class_="scenario-selector-controls",
            ),
            style=(
                "display:flex;"
                "align-items:center;"
                "justify-content:flex-end;"
                "margin-top:8px;"
            ),
            class_="scenario-selector-bar",
        ),
        # style="padding:10px 20px; border-bottom:1px solid #ccc;",
        class_="app-header-panel",
    ),
    # EXPLORER NAVSET PAGES
    ui.div(
        ui.navset_tab(
            ui.nav_panel("Primary energy", primary_energy_ui),
            ui.nav_panel("Energy demand", demand_ui),
            ui.nav_panel("Electricity generation", elec_ui),
            ui.nav_panel("Emissions", emissions_ui),
            ui.nav_panel("Energy service demand", esd_ui),
            ui.nav_panel("Infeasibilities", dummy_ui),
        ),
        class_="navset-large",
    ),
)


app_ui = ui.div(
    ui.div(ui.div(class_="loader"), id="page-loader-parent"),
    app_ui,
    # Inserts a tag to enable the iframe to dynamically resize to this point.
    ui.HTML("<div data-iframe-height></div>"),
    id="app-parent",
)
