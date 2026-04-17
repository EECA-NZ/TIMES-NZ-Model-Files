"""
Executes building Veda files for new electricity techs
"""

from prepare_times_nz.stage_4.electricity.fixed_plant_adjustments import (
    main as write_fixed_install_adjustments,
)
from prepare_times_nz.stage_4.electricity.new_generation import (
    main as write_new_ele_techs,
)
from prepare_times_nz.stage_4.electricity.new_storage import (
    main as write_new_ele_storage,
)
from prepare_times_nz.stage_4.electricity.renewable_curves import (
    main as write_renewable_curves,
)

# generation technologies
write_new_ele_techs()
# battery technologies
write_new_ele_storage()
# renewable availability curves
write_renewable_curves()
# fixed adjustment dates for availability.
# note this depends on renewable curves so must always run afterwards
write_fixed_install_adjustments()
