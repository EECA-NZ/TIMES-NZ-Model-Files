NIWA weather files for the solar availability-factor workflow live in this directory.

Preferred source:
- MBIE, "Weather files for Aotearoa New Zealand" (last updated 30 October 2024): https://www.building.govt.nz/getting-started/climate-change-work-programme/resources/weather-files-aotearoa-new-zealand

Licensing and attribution:
- Building Performance copyright page: https://www.building.govt.nz/about-building-performance/copyright
- The repo stores these files with attribution to the Ministry of Business, Innovation and Employment (MBIE), consistent with the site's Creative Commons Attribution 4.0 notice.

Expected inputs:
- `tmy3_epw.tar.gz`

Recommended maintenance workflow:
1. Download the present-climate TMY3 ZIP from the MBIE page in a browser if scripted download is blocked.
2. Run `python3 PREPARE-TIMES-NZ/scripts/stage_3_scenarios/electricity/niwa_tmy3_download.py --zip-path /path/to/tmy3.zip` to validate the ZIP and convert it into `tmy3_epw.tar.gz`.
3. Commit `tmy3_epw.tar.gz`.
4. Run the stage-3 solar tasks to regenerate `data_intermediate/stage_3_scenario_data/electricity/solar_af/` and `data_intermediate/stage_3_scenario_data/electricity/renewable_curves.csv`.
