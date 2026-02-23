"""TODO: implement an automated TIMES configuration script"""

# pylint: disable=all

# libraries
import os
import sys
import time

# get custom libraries
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(current_dir, "..", "library"))
from archive_helpers import write_workbook

# Defining files to write

base_year_files = [
    "BY_Trans",
    "VT_NI_ELC_V4",
    "VT_NI_IND_V2",
    "VT_NI_OTH_V4",
    "VT_NI_PRI_V4",
    "VT_NI_TRA_V4",
    "VT_SI_ELC_V4",
    "VT_SI_IND_V2",
    "VT_SI_OTH_V4",
    "VT_SI_PRI_V4",
    "VT_SI_TRA_V4",
]
settings_files = ["SysSettings"]

subres_files = [
    "SubRES_TMPL/SubRES_NewTech_AGR_KEA",
    "SubRES_TMPL/SubRES_NewTech_AGR_KEA_Trans",
    "SubRES_TMPL/SubRES_NewTech_AGR_TUI",
    "SubRES_TMPL/SubRES_NewTech_AGR_TUI_Trans",
    "SubRES_TMPL/SubRES_NewTech_ELC_KEA",
    "SubRES_TMPL/SubRES_NewTech_ELC_TUI",
    "SubRES_TMPL/SubRES_NewTech_RC",
    "SubRES_TMPL/SubRES_NewTechs_Industry",
    "SubRES_TMPL/SubRES_NewTechs_Industry_Trans",
    "SubRES_TMPL/SubRES_NewTransport-KEA",
    "SubRES_TMPL/SubRES_NewTransport-TUI",
]

supp_files = [
    "SuppXLS/Scen_AF_Renewable",
    "SuppXLS/Scen_Base_constraints",
    "SuppXLS/Scen_Carbon_Budgets",
    "SuppXLS/Scen_Cohesive",
    "SuppXLS/Scen_Individualistic",
    "SuppXLS/Scen_LoadCurve_COM-FR",
    "SuppXLS/Scen_RE_Potentials",
    "SuppXLS/Scen_WEM_WCM",
    "SuppXLS/Trades/ScenTrade_TRADE_PARMS",
    "SuppXLS/Trades/ScenTrade__Trade_Links",
]

all_times_nz_files = base_year_files + settings_files + supp_files + subres_files


def write_files():
    files_to_write = all_times_nz_files
    for file in files_to_write:
        write_workbook(file)


start_time = time.time()
write_files()
end_time = time.time()
execution_time = end_time - start_time
print(f"Writing these workbooks took {execution_time:.4f} seconds")
