"""
Defines the ui for the internal app
"""

from shiny import ui
from times_nz_internal_qa.app.app_module_demand import demand_ui
from times_nz_internal_qa.app.app_module_dummies import dummy_ui
from times_nz_internal_qa.app.app_module_elec import elec_ui
from times_nz_internal_qa.app.app_module_emissions import emissions_ui

app_ui = ui.page_fluid(
    # quick css:
    # these tags style the navbar headings
    ui.tags.style(""".navset-large .nav-link {font-size: 1.6rem;}"""),
    # These tags style the TIMES-101 popup
    ui.tags.style(
        """
                  .modal-dialog {
                  max-width: 900px !important;   /* set modal width */
                  margin-top: 5vh !important;   /* distance from top (smaller = higher) */
                  }
                  .modal-body p {
                  margin-bottom: 0.75rem;        /* control paragraph spacing */
                  }
                  """
    ),
    # actual UI from here:
    ui.div(
        ui.h1("TIMES-NZ 3.0 Alpha"),
        ui.h1("NOT FOR RELEASE - QA INCOMPLETE", style="color:red; font-weight:bold;"),
        ui.input_action_button("info_btn_101", "TIMES-NZ 101"),
        ui.input_action_button("info_btn_use", "Using this app"),
        style="display:flex; align-items:center; justify-content:space-between;",
    ),
    ui.div(
        ui.navset_tab(
            ui.nav_panel("Infeasibilities", dummy_ui),
            ui.nav_panel("Emissions", emissions_ui),
            ui.nav_panel("Energy demand", demand_ui),
            ui.nav_panel("Electricity generation", elec_ui),
        ),
        class_="navset-large",
    ),
)
