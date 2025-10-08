"""
Defines the ui for the internal app
"""

import pandas as pd
from shiny import ui
from times_nz_internal_qa.app.dummy_processes import dummy_ui
from times_nz_internal_qa.app.electricity import elec_ui
from times_nz_internal_qa.app.energy_demand import demand_ui
from times_nz_internal_qa.utilities.filepaths import FINAL_DATA

ele_gen_data = pd.read_csv(FINAL_DATA / "elec_generation.csv", low_memory=False)


def get_df_options(df, variable):
    """
    returns all the options for variable in df
    as a list. useful for dynamic app selection.
    """
    df = df.copy()
    return df[variable].unique().tolist()


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
        ui.input_action_button("info_btn", "TIMES-NZ 101"),
        style="display:flex; align-items:center; justify-content:space-between;",
    ),
    ui.em("Internal result testing. Currently only Traditional scenario"),
    ui.div(
        ui.navset_tab(
            ui.nav_panel("Electricity", elec_ui),
            ui.nav_panel("Energy demand", demand_ui),
            ui.nav_panel("Infeasibilities", dummy_ui),
        ),
        class_="navset-large",
    ),
)
