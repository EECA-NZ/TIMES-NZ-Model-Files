# Domain violations in steady v3.0.9 solve

Source: `SOLVE-TIMES-NZ/build/solves/steady-v3.0.9-20261126T194821Z/steady.lst`
(154 GAMS error 170 "Domain violation" entries, all raised while reading `output.dd`).

No fixes have been applied yet.

## 1. `COM_FR` (60): typo in ag load curves

- `PREPARE-TIMES-NZ/data_raw/coded_assumptions/ag_forest_fish_demand/ag_curves_mpm.csv`
  has spring rows `SPR-WK` and `SPR-WE`. Valid timeslices are `SPR-WK-` and `SPR-WE-`.
- 15 ag commodities x 2 timeslices x 2 islands. The invalid rows are dropped, so spring
  has no share in the 2024 mobile ag load shape (a real distortion).
- Fix: rename the 6 CSV rows (3 commodity groups x 2 timeslices) to add the trailing hyphen.

## 2. `FLO_EMIS` (8) and `TOP` (4): stale Ngawha process names

- `PREPARE-TIMES-NZ/data_raw/user_config/base_year/VT_TIMESNZ_ELC.toml`,
  `[NgawhaEmissionFactorAdjustments]` targets `ELC_Geothermal_GEO_Ngawha(oec1-3)` and `(oec4)`.
- Current processes are `ELC_Geo_NgawhaOEC13` and `ELC_Geo_NgawhaOEC4`, so the adjustment
  is silently ignored. Ngawha stays at 25.56 kt/PJ instead of falling to 0 by 2026.
- Fix: correct the two names in the toml. Expect Ngawha emissions to change.

## 3. `PRC_ACTUNT` (82): industry future techs

- 41 future industry techs x 2 islands, e.g. `'NI'.'ALUM-ELC-HPSH-SH_LOW'.'ALUM-ELC-HPSH-SH_LOW_DEMO'.'PJ'`.
- `PREPARE-TIMES-NZ/src/prepare_times_nz/stage_4/industry/new_techs.py` (~line 169) sets
  `PrimaryCG = <tech>_DEMO`. xl2times never declares that group, so the entries are dropped.
- Practical impact looks small (e.g. `DARY-ELC-HPPH-PH_LOW` solves normally).
- Likely fix (untested): set `PrimaryCG` to the standard `DEMO` suffix, which xl2times expands
  itself (`transforms.py` ~1579). First confirm `DEMO` is in `default_pcg_suffixes`.
- Side finding: about 12 of these techs have no output commodity in the DD (e.g.
  `ALUM-ELC-HPSH-SH_LOW`, whose output `ALUM-SH_LOW` is not declared; also STEEL, MEAT, METH,
  MNRL, OTHR, UREA, WOOD `-ELC-HPSH-SH_LOW`, `MINE-ELC-BOILR-PH_LOW`, `CHEM-ELC-EFURNC-PH_HIGH`).
  They are dead (`VAR_Act` = 0). The PrimaryCG fix will not change this.
