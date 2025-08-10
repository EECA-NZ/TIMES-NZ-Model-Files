"""
We have explicitly set our load curves to always peak at 6pm for every season.
This isn't perfect, but is quite close.

This script:

1) Creates base_year load curves using base year GXP data, mapping this to islands.
   These load curves will be applied to the total base year electricity demand for
   every sector.

   (This was the TIMES 2.0 method.)
   We are calibrating our load curves rather than representing each sector.
   I am not sure I like this approach, but oh well.

2) Identifies residential GXPs and uses 2023 residential GXP demand per timeslice.
   This is only for forming COM_FR for residential demand. We do NOT adjust these
   per island. We will maintain these residential shares.

Potential additional features (not yet implemented):

1) Load RBS data to distinguish residential load curves more fully.
   These should be based on the base year, but distinguish commodities per timeslice.

   This would allow for:
     a) Better representation of how reducing space heating demand affects peaks.
     b) Assessment of shape impact when changing demand by commodity
        (e.g. increased cooling).

   Since we don't currently project different residential commodities at different
   rates, b) is currently irrelevant—but a) is useful.

Outputs:

- base_year_load_curves (could also just generate curves by year and filter later)
- load_curves_residential
- yrfr

Potential checking outputs:

- base_year peak (by applying load curves to total demand)—
  this shows the 6GW peak load we're representing.
"""

from prepare_times_nz.stage_2 import load_curves

if __name__ == "__main__":
    load_curves.main()

# Tests
# load_curves.test_average_loads()
# load_curves.estimate_res_real_peak()
