# Objective-function differences: Steady case

This note records the first comparison between the TOML/xl2times-generated
Steady solve and its VEDA-generated reference result.  It is an investigation
record, not yet an explanation of the difference.

## Compared results

| Result | File |
| --- | --- |
| TOML/xl2times solve | `build/solves/steady-20261028T060716Z/steady.vd` |
| VEDA reference | `veda_ground_truths/steady-v309xl2times-test/steady-v309xl2times-test_2810.vd` |

| Measure | TOML/xl2times | VEDA | Difference (new - VEDA) |
| --- | ---: | ---: | ---: |
| Objective (`ObjZ`, MioNZ$) | 1,469,035.4824 | 1,470,450.0034 | -1,414.5210 (-0.0962%) |

The TOML/xl2times result is therefore close, but is not yet equivalent to the
VEDA result.

### Effect of the 15-significant-digit precision rebuild

The first generated solve used xl2times' upstream 10-significant-digit DD
formatting and had an objective of 1,469,035.4675 MioNZ$. The rebuilt solve
uses the project compatibility wrapper's 15-significant-digit formatting and
has an objective of 1,469,035.4824 MioNZ$: an increase of only 0.0149 MioNZ$.
The gap to VEDA has therefore reduced by 0.0149 MioNZ$, from 1,414.5359 to
1,414.5210 MioNZ$.

The precision correction is necessary for input equivalence, but it does not
explain the remaining objective difference. The annual `TOTCO2` profile also
remains materially different after the rebuild: generated emissions are 1.36%
lower in 2030 and 25.94% lower in 2050. The remaining investigation should
therefore focus on effective constraints, bounds, topology, and DD update
order rather than numeric formatting.

## Objective decomposition

The following values are the `REG_WOBJ` result records.  They show where the
net objective difference appears, rather than identifying its original input
cause.

| Region | Cost component | Difference (MioNZ$) |
| --- | --- | ---: |
| NI | investment | +1,474.7168 |
| SI | investment | -368.5211 |
| NI | fixed | +29.0239 |
| SI | fixed | -78.9063 |
| NI | variable | -1,923.7843 |
| SI | variable | -193.3280 |
| NI | variable externality | -305.0144 |
| SI | variable externality | -48.7226 |
| **Total** |  | **-1,414.5359** |

Variable-cost differences dominate the lower objective.  Investment decisions
also differ materially, but offset part of that reduction.

## Main result differences observed

### Fuel and externality costs

`COST_FLO` is lower in the generated solve by 6,561.7 MioNZ$ across common
result keys.  The largest individual differences are reduced imported-fuel
costs, principally NI diesel imports (`IMPDSL`) in 2040--2050, with smaller
differences for LNG and petrol imports.  `COST_COMX` is lower by 1,169.0
MioNZ$, almost entirely from `TOTCO2`.

These are result differences, not evidence that the fuel-cost input data are
wrong.  They may instead result from different technology and fuel choices.

### Investment and capacity choices

`COST_INV` is higher by 1,344.4 MioNZ$ across common result keys.  The largest
individual records include electric transport technologies, notably
`T_P_CBEVELC_HIGH` and `T_P_CBEVELC_MED`.  Fixed-cost differences are much
smaller overall (-132.6 MioNZ$), though individual technologies differ.

### Time-slice activity

The files contain large `VAR_ActM` differences, particularly for South Island
commercial biomass boilers and `H2_PEM`.  For example, some 2024 H2 PEM
time-slice result records differ by hundreds of thousands.

These records must not yet be read as equivalent annual-energy differences:
`VAR_ActM` is reported by time slice and can change sharply with the way
time-slice activity is represented.  The `COM_FR` records in the generated
`output.dd` match the VEDA `loadcurve.dd` records, apart from serialisation
details such as quoting and numeric precision.  The load curve is therefore
not currently evidenced as the cause.

## What has not been established

- The comparison does not identify a defective workbook, TOML group, or
  xl2times transform.
- The large `VAR_ActM` differences have not been converted into an annual,
  duration-weighted comparison.
- It has not been shown whether a differing result arises from an actual
  effective GAMS input difference or from an alternative, near-optimal model
  solution.

## Exploring possible causes

### Commercial-coal `PRC_RESID` check

An initial comparison incorrectly reported five non-zero `PRC_RESID` records
as missing from generated `output.dd`.  Inspection of the DD file actually
staged for the compared solve confirms that all five are present and agree
with the values in the prepared commercial workbook and VEDA DD input.  They
represent residual base-year stock for existing commercial coal boilers:

| Region | Process | VEDA `PRC_RESID` |
| --- | --- | ---: |
| NI | `C_OTH_WH_BOILER_COA` | 0.0000073388 |
| SI | `C_OFFC_WH_BOILER_COA` | 0.0000892610 |
| SI | `C_OTH_WH_BOILER_COA` | 0.0000023177 |
| SI | `C_WSR_SH_BOILER_COA` | 0.0000469226 |
| SI | `C_WSR_WH_BOILER_COA` | 0.0000350433 |

The source is `VT_TIMESNZ_COM.xlsx`, `COM_Demand`, `~FI_T`
`CommercialProcessParameters`; xl2times raw-table extraction also retains
each value.  VEDA did not generate these values.

The remaining representation difference is that xl2times adds a zero
`PRC_RESID` record in 2048 for each process (base year 2023 plus the 25-year
technical life).  VEDA's DD input does not contain an explicit corresponding
zero record.  xl2times contains this residual-stock expiry fix-up, although
its source code notes that TIMES may already handle the expiry.  This is a
representation difference, but it is not evidence that the original non-zero
stock was lost.

### Imported diesel, petrol, and LNG

The DD records for `IMPDSL`, `IMPPET`, and `IMPLNG` were compared between the
DD file staged for the generated solve and the complete VEDA DD set.  There
is no difference in the import-price records or other numeric parameter
records for these processes.  In particular, the `IRE_PRICE` records agree
at their supplied 2023, 2030, and 2050 values, and the diesel and petrol
process topology, time-slice assignment, activity unit, and IRE mapping also
agree.

LNG has a representation difference.  VEDA declares `IMPLNG_NRGO` as the
activity-unit commodity and maps it to `LNG` through `COM_GMAP`; xl2times
uses `LNG` directly as the `PRC_ACTUNT` commodity.  Both inputs retain the
same `IMPLNG -> LNG` output topology, annual time-slice assignment, IRE
mapping, and import-price record.  This is therefore not currently evidence
of a price or physical-flow mismatch, but it is a structural conversion
difference to retain in the compatibility inventory.

The lower diesel, petrol, and LNG costs in the solve results consequently
appear to be effects of different fuel and technology decisions elsewhere in
the model, rather than differences in these import-process prices.

### South Island winter energy margin (`WEM_SI`)

`WEM_SI` was checked as a possible explanation for the lower-cost,
lower-emissions solution.  The staged generated DD and VEDA `wem_wcm.dd`
contain the same constraint input:

- `UC_R_EACH` membership for both NI and SI;
- the same 80 South Island generation-technology `UC_CAP` coefficients;
- the same two SI `G_ELC_LV` / `ELCDD` seasonal `UC_FLO` coefficients;
- the same three `UC_RHSRTS` terms: NI 2024 lower bound zero, SI year-zero
  lower bound five, and SI 2024 lower bound zero.

Numeric differences are only output precision.  The generated DD additionally
includes the constraint description text.  `WEM_SI` is therefore not missing
or relaxed in the xl2times input.

## Next investigation steps

1. Compare effective final GAMS parameter records for the remaining main
   drivers: `TOTCO2`, the affected electric transport technologies, and the
   relevant competing technology choices.
2. Check overlapping DD records and their effective combination order.  The
   TOML case groups workbooks differently from the VEDA manifest, and ordering
   matters where files update the same GAMS record.
3. Make a duration-weighted, annual comparison of `VAR_ActM` before treating
   the large time-slice values as a model-activity incompatibility.
4. Once an input-level difference is found, reduce it to a small reproducible
   test before changing either PREPARE-TIMES-NZ or the xl2times compatibility
   layer.
