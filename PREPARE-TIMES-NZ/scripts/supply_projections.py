"""Just runs gas projection processing"""

from prepare_times_nz.stage_3.biomass_forecasts import main as biomass_projections
from prepare_times_nz.stage_3.gas_forecasts import main as gas_projections

gas_projections()
biomass_projections()
