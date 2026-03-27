
# Availability curves

This section details capacity factors used across all TIMES-NZ generation types.

## Dispatchable

For dispatchable plants, the capacity factor estimate is considered an annual upper bound. However, they are free to generate at different times of year depending on system needs.

```{csv-table} Dispatchable plant capacity factor assumptions
:header-rows: 1
:name: tab-capacity_factors
Plant Type,Capacity Factor (%)
Biogas,75
Diesel (peakers),2
Huntly Rankine units,37
Natural gas (CCGT),65
Natural gas (OCGT),33
```
We note that this is a limitation for CCGT plants, as this method allows them too much flexibility in how quickly they might begin or halt generation.

## Baseload

Geothermal and cogeneration plants are considered "baseload". This means that their generation within the model is fixed at every time of year and day according to the below assumptions

```{csv-table} Baseload plant capacity factors
:header-rows: 1
:name: tab_baseload_capacity factors
Plant Type,Capacity Factor (%)
Biomass (cogeneration),55
Coal (cogeneration),55
Natural gas (cogeneration),55
Geothermal (cogeneration),80
Geothermal (electricity),88
```

In the model, these plants will not flex generation up or down depending on demand.

## Solar

Solar availability factors are generated in the stage-3 electricity workflow from NIWA typical meteorological year (TMY) weather files using the PVWatts model in NREL PySAM, then converted into TIMES-NZ timeslices. The workflow is implemented in `solar_prepare_epw.py`, `solar_run_hourly_profiles.py`, and `solar_build_curves.py`, and the resulting curves are consumed in stage 4 by `renewable_curves.py`.

```{note}
All solar availability curves are considered fixed, rather than upper bounds. This means solar will always generate at the listed output in the model, and not flex depending on demand. In stage 4 the rows are written as `NCAP_AF` with `LimType = FX`, so the model does not treat solar as a spillable upper bound in the way it treats wind and some hydro constraints.
```

**Data source and preprocessing.** The weather input is a bundled NIWA TMY2 EPW archive (`data_raw/external_data/niwa/tmy2_epw.tar.gz`) containing one EPW file for each of 18 climate zones. The preparation step copies or extracts those files into stage-3 storage and normalizes EPW hour fields if needed before simulation. EPW format details are documented by SAM[^sam_weather]. MBIE also hosts a newer NIWA TMY3 weather-file release[^niwa_tmy3]. The current workflow still uses the older bundled TMY2 EPW dataset.

**PVWatts configuration.** Solar simulations use PySAM's `Pvwattsv8` model via the project dependency `nrel-pysam = "^7.1"` in `pyproject.toml`, which corresponds to `>=7.1.0,<8.0.0`. Each solar archetype is simulated as a 1 kW DC system, so the hourly PVWatts output can be used directly as `generation_kw_per_kw`. We assume that all utility-scale plants in the generation stack are single-axis tracking, and that commercial and industrial distributed solar is bifacial. The following PVWatts settings are applied:

```{list-table} Configured solar PVWatts archetypes
:header-rows: 1
:name: tab_solar_pv_scenarios
* - `Tech_TIMES`
  - Configured description
  - Array type
  - Key differences from other archetypes
* - `SolarDistSmall`
  - Residential rooftop PV
  - `fixed_roof_mount`
  - `Bifaciality = 0`, `Albedo = 0.2`
* - `SolarDistBifacial`
  - Commercial fixed bifacial rooftop PV
  - `fixed_roof_mount`
  - `Bifaciality = 0.65`, `Albedo = 0.3`
* - `SolarTrack`
  - Utility-scale single-axis backtracking bifacial PV
  - `single_axis_backtracking`
  - `Bifaciality = 0.65`, `Albedo = 0.2`
```

All three archetypes currently use:

- `SystemCapacityKW = 1.0`
- `TiltDeg = 30`
- `AzimuthDeg = 0`
- `LossesPercent = 9.03`
- `InvEffPercent = 96`
- `ModuleType = standard`
- `DcAcRatio = 1.2`
- `Gcr = 0.4`
- `UseWeatherFileAlbedo = False`

`LossesPercent` uses the standard PVWatts/SAM system-losses input[^sam_losses]. In this workflow it is set to 9.03% so the average generation across regions aligns with the existing EECA Solar Power Calculator.

**Conversion to TIMES timeslices.** For each solar archetype $s$, climate zone $z$, and hour $h$, PVWatts returns hourly generation $g_{s,z,h}$ in kW from the 1 kW DC system. The zone-level TIMES availability factor for timeslice $\tau$ is:

```{math}
AF_{s,z,\tau} = \frac{1}{|H_\tau|}\sum_{h \in H_\tau} g_{s,z,h}
```

where $H_\tau$ is the set of hours mapped to that TIMES timeslice. In the implementation this is the mean of `generation_kw_per_kw` over all rows in the timeslice.

The timeslice mapping is the shared project mapping used elsewhere in the electricity workflow:

- season: `SUM` = December-February, `FAL` = March-May, `WIN` = June-August, `SPR` = September-November
- day type: `WK` weekday, `WE` weekend
- time of day: `D` = 07:00-17:00, `P` = 18:00, `N` = all remaining hours, using New Zealand wall-clock time

To assign weekday, weekend, and time-of-day labels consistently, the workflow applies the shared timeslice mapping using the configured TIMES-NZ model base year calendar. The EPW weather files are treated as fixed New Zealand standard time (`UTC+12`), and each interval-start hour is converted with the `Pacific/Auckland` timezone before assigning timeslices.

The solar peak timeslice can be much lower than the daytime timeslice, because `P` is only the 18:00 wall-clock hour, so it captures shoulder-period. SAM notes that its one-axis tracking algorithm assumes a rotation limit of +/-45 degrees from the horizontal[^sam_losses]. For `SolarTrack`, the use of single-axis backtracking further reduces late-afternoon output relative to a tracker that follows the sun more aggressively.

**Island aggregation and model input.** TIMES-NZ uses island-level curves, so the zone-level availability factors are combined with configurable weights from `SolarZoneWeights.csv`. For island $i$:

```{math}
AF_{s,i,\tau} = \frac{\sum_{z \in i} w_z AF_{s,z,\tau}}{\sum_{z \in i} w_z}
```

The weights are normalized within each island before aggregation. The current default is equal weighting for every zone within the North Island and every zone within the South Island, so the derived island-level availability factors are simple averages of the zone-level values within each island.

The tables below show the current generated island-level availability factors under the default PVWatts assumptions and default equal zone weights.

```{csv-table} SolarDistSmall: Residential distributed solar availability factors
:header-rows: 1
:name: tab_solar_availability_dist
Season,Day Type,Time of Day,North Island,South Island
Autumn,Weekend,Day,31.0%,29.5%
Autumn,Weekend,Night,0.0%,0.1%
Autumn,Weekend,Peak,3.1%,5.2%
Autumn,Weekday,Day,31.0%,27.7%
Autumn,Weekday,Night,0.0%,0.0%
Autumn,Weekday,Peak,3.0%,4.5%
Spring,Weekend,Day,37.4%,36.4%
Spring,Weekend,Night,0.1%,0.1%
Spring,Weekend,Peak,5.6%,9.3%
Spring,Weekday,Day,38.0%,37.9%
Spring,Weekday,Night,0.1%,0.2%
Spring,Weekday,Peak,6.0%,10.1%
Summer,Weekend,Day,40.0%,41.0%
Summer,Weekend,Night,0.3%,0.7%
Summer,Weekend,Peak,14.8%,19.5%
Summer,Weekday,Day,42.0%,41.4%
Summer,Weekday,Night,0.3%,0.7%
Summer,Weekday,Peak,15.3%,19.8%
Winter,Weekend,Day,22.3%,20.7%
Winter,Weekend,Night,0.0%,0.0%
Winter,Weekend,Peak,0.0%,0.0%
Winter,Weekday,Day,25.2%,22.0%
Winter,Weekday,Night,0.0%,0.0%
Winter,Weekday,Peak,0.0%,0.0%
**Annual**,,,**15.7%**,**15.2%**
```

```{csv-table} SolarDistBifacial: Fixed commercial bifacial solar availability factors
:header-rows: 1
:name: tab_solar_availability_dist_bifacial
Season,Day Type,Time of Day,North Island,South Island
Autumn,Weekend,Day,32.9%,31.2%
Autumn,Weekend,Night,0.0%,0.1%
Autumn,Weekend,Peak,3.4%,5.6%
Autumn,Weekday,Day,32.9%,29.3%
Autumn,Weekday,Night,0.0%,0.0%
Autumn,Weekday,Peak,3.3%,4.8%
Spring,Weekend,Day,40.0%,38.7%
Spring,Weekend,Night,0.1%,0.2%
Spring,Weekend,Peak,6.6%,10.4%
Spring,Weekday,Day,40.6%,40.2%
Spring,Weekday,Night,0.1%,0.2%
Spring,Weekday,Peak,7.1%,11.3%
Summer,Weekend,Day,43.0%,43.8%
Summer,Weekend,Night,0.5%,0.9%
Summer,Weekend,Peak,17.0%,21.7%
Summer,Weekday,Day,45.1%,44.1%
Summer,Weekday,Night,0.5%,0.9%
Summer,Weekday,Peak,17.6%,22.0%
Winter,Weekend,Day,23.7%,21.7%
Winter,Weekend,Night,0.0%,0.0%
Winter,Weekend,Peak,0.0%,0.0%
Winter,Weekday,Day,26.7%,23.1%
Winter,Weekday,Night,0.0%,0.0%
Winter,Weekday,Peak,0.0%,0.0%
**Annual**,,,**16.8%**,**16.1%**
```

```{csv-table} SolarTrack: Utility-scale tracking solar availability factors
:header-rows: 1
:name: tab_solar_availability_utility_track
Season,Day Type,Time of Day,North Island,South Island
Autumn,Weekend,Day,37.7%,35.9%
Autumn,Weekend,Night,0.0%,0.1%
Autumn,Weekend,Peak,6.9%,12.0%
Autumn,Weekday,Day,37.6%,33.5%
Autumn,Weekday,Night,0.0%,0.1%
Autumn,Weekday,Peak,6.8%,9.4%
Spring,Weekend,Day,45.6%,43.5%
Spring,Weekend,Night,0.2%,0.3%
Spring,Weekend,Peak,12.4%,19.4%
Spring,Weekday,Day,46.2%,45.3%
Spring,Weekday,Night,0.2%,0.3%
Spring,Weekday,Peak,13.2%,21.0%
Summer,Weekend,Day,47.8%,48.5%
Summer,Weekend,Night,0.7%,1.5%
Summer,Weekend,Peak,30.6%,37.8%
Summer,Weekday,Day,50.5%,48.8%
Summer,Weekday,Night,0.7%,1.6%
Summer,Weekday,Peak,32.8%,38.0%
Winter,Weekend,Day,26.8%,24.8%
Winter,Weekend,Night,0.0%,0.0%
Winter,Weekend,Peak,0.0%,0.0%
Winter,Weekday,Day,30.4%,26.3%
Winter,Weekday,Night,0.0%,0.0%
Winter,Weekday,Peak,0.0%,0.0%
**Annual**,,,**19.3%**,**18.5%**
```

Detailed timeslice values are generated by the workflow and written to `data_intermediate/stage_3_scenario_data/electricity/solar_af/timeslices/solar_availability_factors.csv`. These generated solar rows replace the static solar rows in `RenewableCurves.csv`, after which stage 4 converts them into model `NCAP_AF` records.

[^sam_losses]: NREL SAM help: Fuel Cell / Photovoltaic System, including the discussion of PVWatts system losses: <https://samrepo.nrelcloud.org/help/fuelcell_pv_system.html>
[^sam_weather]: NREL SAM help: weather file format: <https://samrepo.nrelcloud.org/help/weather_format.html>
[^niwa_tmy3]: MBIE-hosted NIWA TMY3 weather files: <https://www.building.govt.nz/assets/Uploads/getting-started/building-for-climate-change/Weather-files-ZIP-files/tmy3.zip>

## Hydro
Hydro electricity generation uses a different approach. Here we assume generation follows seasonal patterns, but generation is capable of flexing within these seasonal restrictions. Because average output within a season is fixed, but able to flex within any give timeperiod, the model should, if necessary, lower hydro output when it is not needed. This allows for higher generation at other points in the season while still meeting seasonal constraints.

```{csv-table} Dispatchable hydro availability assumptions
:header-rows: 1
:name: tab_hydro_availability
Season,North Island,South Island
Sumner,45.3%,60.5%
Autumn,49.6%,56.1%
Winter,38.1%,54.0%
Spring,56.9%,64.0%
**Annual**,**47.5%**,**58.6%**
```
These figures have been extracted from assumptions used for TIMES 2.0. Note that run-of-river hydro is not afforded the same flexibility within the model.

## Wind

Onshore wind availability curves are based on analysis of the availability of New Zealand’s wind farms since 2020. These are then scaled up slightly to meet a 38% annual average, as we assume future generation may perform better than existing plants as technology improves. We keep the same generation curves for offshore wind, but scaled up across every timeslice to give an annual availability assumption of 50%.


```{eval-rst}
.. admonition:: Wind peak modelling
   :class: note

   There is a difference between modelled generation during "peak" timeslices, or the highest-demand hour in every day, and the "peak constraint", which refers to the highest demand in any given year.

   In the case of wind, we assume a reasonably high output during peak timeslices, but a lower peak contribution rate. Peak contribution rates are described in more detail in the Technical Parameters section.
```

Currently, we use the same factors for the North and South Islands.

```{csv-table} Wind availability factors
:header-rows: 1
:name: tab_wind_availability
Season,Day Type,Time of Day,Onshore,Offshore
Autumn,Weekend,Day,34.2%,44.9%
Autumn,Weekend,Night,32.6%,42.9%
Autumn,Weekend,Peak,35.8%,47.1%
Autumn,Weekday,Day,33.9%,44.6%
Autumn,Weekday,Night,33.8%,44.5%
Autumn,Weekday,Peak,34.9%,45.9%
Spring,Weekend,Day,43.3%,57.0%
Spring,Weekend,Night,41.1%,54.1%
Spring,Weekend,Peak,43.8%,57.6%
Spring,Weekday,Day,44.6%,58.7%
Spring,Weekday,Night,43.0%,56.5%
Spring,Weekday,Peak,47.2%,62.0%
Summer,Weekend,Day,37.9%,49.9%
Summer,Weekend,Night,35.8%,47.2%
Summer,Weekend,Peak,42.0%,55.3%
Summer,Weekday,Day,36.9%,48.5%
Summer,Weekday,Night,35.8%,47.2%
Summer,Weekday,Peak,39.8%,52.3%
Winter,Weekend,Day,39.2%,51.6%
Winter,Weekend,Night,37.0%,48.7%
Winter,Weekend,Peak,38.2%,50.3%
Winter,Weekday,Day,38.5%,50.6%
Winter,Weekday,Night,38.0%,50.0%
Winter,Weekday,Peak,38.7%,50.9%
**Annual**,,,**38%**,**50%**
```
