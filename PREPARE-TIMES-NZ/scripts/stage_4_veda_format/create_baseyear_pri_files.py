"""
Module executes all the oil and gas veda transformations

Currently just does the oil gas veda scripts
"""

from prepare_times_nz.stage_4.biofuels import main as biofuels_veda
from prepare_times_nz.stage_4.oil_and_gas import main as oil_gas_veda

oil_gas_veda()
biofuels_veda()
