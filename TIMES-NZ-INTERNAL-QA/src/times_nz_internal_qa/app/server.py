"""
server functions for app.py
"""

from times_nz_internal_qa.app.app_module_demand import demand_server
from times_nz_internal_qa.app.app_module_dummies import dummy_server
from times_nz_internal_qa.app.app_module_elec import elec_server
from times_nz_internal_qa.app.app_module_emissions import emissions_server
from times_nz_internal_qa.app.app_module_readme_docs import info_server
from times_nz_internal_qa.app.app_module_select_scenario import scenario_select_server


def server(inputs, outputs, session):
    """
    Parent server, which includes some high-level processing items,
    and also combines all server modules from specific pages
    """

    # information popups
    info_server(inputs, outputs, session)

    # Scenarios
    selected_scens = scenario_select_server(inputs, outputs, session)

    # modules
    demand_server(inputs, outputs, session, selected_scens)
    dummy_server(inputs, outputs, session, selected_scens)
    elec_server(inputs, outputs, session, selected_scens)
    emissions_server(inputs, outputs, session, selected_scens)
