"""
server functions for app.py
"""

from shiny import reactive, ui
from times_nz_internal_qa.app.dummy_processes import dummy_server
from times_nz_internal_qa.app.electricity import elec_server
from times_nz_internal_qa.app.energy_demand import demand_server
from times_nz_internal_qa.utilities.filepaths import ASSETS

readme_times_101 = (ASSETS / "times_101.md").read_text(encoding="utf-8")


def server(inputs, outputs, session):
    """Combine all server modules"""

    @reactive.effect
    @reactive.event(inputs.info_btn)
    def _():
        ui.modal_show(
            ui.modal(
                ui.markdown(readme_times_101),
                title="TIMES-NZ 101",
                easy_close=True,  # user can click outside or press Esc to close
                footer=ui.modal_button("Close"),
            )
        )

    demand_server(inputs, outputs, session)
    dummy_server(inputs, outputs, session)
    elec_server(inputs, outputs, session)
