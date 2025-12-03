"""
Runs all industry newtechs
"""

from prepare_times_nz.stage_4.industry.eaf import main as eaf
from prepare_times_nz.stage_4.industry.new_demand import main as new_demand
from prepare_times_nz.stage_4.industry.new_techs import main as new_techs

if __name__ == "__main__":
    new_techs()
    new_demand()
    eaf()
