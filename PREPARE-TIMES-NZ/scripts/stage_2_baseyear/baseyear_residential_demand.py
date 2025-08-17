"""

# Will extract this module docstring to an actual doco file at some point

Builds and applies a residential space‑heating disaggregation model
for EEUD data.

This module provides functions to:

  1. Load and clean StatsNZ census dwelling & heating data.
  2. Aggregate private dwelling types into standardized categories.
  3. Compute normalized heating‑technology shares by region.
  4. Merge in assumptions: floor area, heating efficiency, HDD.
  5. Build a space‑heating demand model to derive fuel demand shares.
  6. Distribute modelled shares against the EEUD residential space‑heating data.
  7. Split Gas/LPG demand between North and South Islands and by fuel.
  8. Saves final results to: residential_space_heating_disaggregation.csv

Constants at the top define filepaths and the base year.

Based on methodology found at:

https://www.sciencedirect.com/science/article/pii/S0378778825004451?ref=pdf_download&fr=RR-2&rr=9677b4c2bbe71c50

Other residential non space-heating demand is disaggregated by
population, and growth is keyed to population

Population data is from census 2023
The population data is disaggregated by dwelling type from census.
This means it's incomplete (not everyone answered dwelling type)
So we should only use the shares, not treat these as regional ERP

"""

from prepare_times_nz.stage_2.disaggregate_residential_demand import main

if __name__ == "__main__":

    main()
