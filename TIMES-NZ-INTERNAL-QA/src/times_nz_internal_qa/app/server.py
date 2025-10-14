"""
server functions for app.py
"""

from shiny import reactive, ui
from times_nz_internal_qa.app.app_module_demand import demand_server
from times_nz_internal_qa.app.app_module_dummies import dummy_server
from times_nz_internal_qa.app.app_module_elec import elec_server
from times_nz_internal_qa.app.app_module_emissions import emissions_server
from times_nz_internal_qa.utilities.filepaths import ASSETS

readme_times_101 = (ASSETS / "times_101.md").read_text(encoding="utf-8")
readme_app_use = (ASSETS / "app_use.md").read_text(encoding="utf-8")


def server(inputs, outputs, session):
    """
    Parent server, which includes some high-level processing items,
    and also combines all server modules from specific pages
    """

    # INFO buttons
    @reactive.effect
    @reactive.event(inputs.info_btn_101)
    def show_times_101():
        ui.modal_show(
            ui.modal(
                ui.markdown(readme_times_101),
                title="TIMES-NZ 101",
                easy_close=True,  # user can click outside or press Esc to close
                footer=ui.modal_button("Close"),
            )
        )

    @reactive.effect
    @reactive.event(inputs.info_btn_use)
    def show_app_use():
        ui.modal_show(
            ui.modal(
                ui.markdown(readme_app_use),
                title="TIMES-NZ Alpha App",
                easy_close=True,  # user can click outside or press Esc to close
                footer=ui.modal_button("Close"),
            )
        )

    demand_server(inputs, outputs, session)
    dummy_server(inputs, outputs, session)
    elec_server(inputs, outputs, session)
    emissions_server(inputs, outputs, session)
