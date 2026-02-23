"""Calls all our Winter Energy Margin scripts
Note: this is called wem_wcm for historical reasons - the wcm refers
to the Winter Capacity Margin, but the WCM settings are entirely in the config file"""

from prepare_times_nz.stage_3.wem_wcm import main as wem_wcm

wem_wcm()
