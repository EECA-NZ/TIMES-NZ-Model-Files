"""
Server functions just to serve the markdown for various info buttons

Note that we do need to ensure all the button ids link correctly to
relevant spots in the UI

Loads in all the markdown as objects for reactives to pull from
"""

# Libraries
from shiny import reactive, ui
from times_nz_internal_qa.utilities.filepaths import ASSETS

# Load markdown inputs

readme_times_101 = (ASSETS / "times_101.md").read_text(encoding="utf-8")
readme_app_use = (ASSETS / "app_use.md").read_text(encoding="utf-8")

info_elc_doc = (ASSETS / "docs/electricity_generation.md").read_text(encoding="utf-8")
info_dum_doc = (ASSETS / "docs/infeasibilities.md").read_text(encoding="utf-8")
info_ems_doc = (ASSETS / "docs/emissions.md").read_text(encoding="utf-8")
info_dem_doc = (ASSETS / "docs/energy_demand.md").read_text(encoding="utf-8")
info_esd_doc = (ASSETS / "docs/energy_service_demand.md").read_text(encoding="utf-8")


# Server function
# pylint:disable = unused-argument
def info_server(inputs, outputs, session):
    """
    Serves all the reactives for markdown-powered info popups
    Not functionalised - we might adjust these later.
    Note that all the ui elements that trigger these are set in the parent UI
    """

    # INFO buttons
    def attach_info(btn_id, content, title):
        @reactive.effect
        @reactive.event(inputs[btn_id])
        def _():
            ui.modal_show(
                ui.modal(
                    ui.tags.h3(title),
                    ui.markdown(content),
                    easy_close=True,
                    size="l",
                    footer=ui.modal_button("Dismiss"),
                )
            )

    # header info buttons
    attach_info("info_btn_101", readme_times_101, "TIMES-NZ 101")
    attach_info("info_btn_use", readme_app_use, "TIMES-NZ Alpha App")
    # Map each tab to its markdown doc
    attach_info("info_elc", info_elc_doc, "Electricity generation")
    attach_info("info_pri", info_elc_doc, "Electricity generation")
    attach_info("info_ems", info_ems_doc, "Emissions")
    attach_info("info_dem", info_dem_doc, "Energy demand")
    attach_info("info_esd", info_esd_doc, "Energy service demand")
    attach_info("info_dum", info_dum_doc, "Infeasibilities")
