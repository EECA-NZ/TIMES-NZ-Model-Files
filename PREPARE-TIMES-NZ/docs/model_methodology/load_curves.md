

## Load curves 

Load curves are calculated in `stage_2/settings/load_curves.py`. 

We have explicitly set our load curves to always peak at 6pm for every season.
This isn't perfect, but is quite close.

We also automatically generate timeslice year fractions in this script,
based on the hour counts from TimeSlice definitions applied to trading periods when extracting half-hourly EA data.

1) Creates base_year load curves using base year GXP data, mapping this to islands.
   These load curves will be applied to the total base year electricity demand for
   every sector.

   (This was the TIMES 2.0 method.)
   We are calibrating our base year load curves to total demand rather than representing each sector.
   

2) Identifies residential GXPs and uses 2023 residential GXP demand per timeslice.
   This is only for forming COM_FR for residential demand. We do NOT adjust these
   per island. We will maintain these residential shares. This was also the TIMES 2 method


Potential additional features (not yet implemented):

1) Load RBS data to distinguish residential load curves more fully.
   These should be based on the base year, but distinguish commodities per timeslice.

   This would allow for:
     a) Better representation of how reducing space heating demand affects peaks.
     b) Assessment of shape impact when changing demand by commodity
        (e.g. increased cooling).

   Since we don't currently project different residential commodities at different
   rates, b) is currently irrelevant—but a) is useful.
