"""
Module executes all the oil and gas veda transformations

Currently just does the oil gas veda scripts
"""

from prepare_times_nz.stage_3.biofuel import main as biofuel_processes_veda
from prepare_times_nz.stage_4.baseyear.oil_and_gas import main as oil_gas_veda
from prepare_times_nz.stage_4.biofuels import main as biofuels_veda

oil_gas_veda()
biofuel_processes_veda()
biofuels_veda()
