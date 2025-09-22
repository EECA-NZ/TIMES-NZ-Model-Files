"""
Executes building Veda files for new electricity techs
"""

from prepare_times_nz.stage_4.electricity.new_generation import (
    main as write_new_ele_techs,
)
from prepare_times_nz.stage_4.electricity.new_storage import (
    main as write_new_ele_storage,
)

# generation technologies
write_new_ele_techs()
# battery technologies
write_new_ele_storage()
