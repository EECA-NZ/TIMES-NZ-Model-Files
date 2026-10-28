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

### Post-preprocessing GDX comparison

To distinguish source-DD differences from the data actually presented to the
TIMES source, diagnostic GDX files were written after input and
preprocessing. The comparison used the same 2250 end-of-time setting for
both exports. It found several structural differences, but no remaining
numeric difference in the user-constraint RHS or coefficient parameters that
would indicate that `WEM`, `WEM_SI`, or the other named constraints have
different mathematical definitions.

| Difference | Assessment for the Steady solve |
| --- | --- |
| `UCN` and `UC_N` | Both GDX files contain the same constraint names, including `WEM` and `WEM_SI`. GDXDIFF reports these set symbols because of representation/order, rather than because constraints were added or removed. |
| `FIRST_VAL` | A temporary scalar used while GAMS fills/interpolates parameters. It is not a model input. |
| `IRE_PRICE` | Eight xl2times-only 9.3-price rows attach South-Island records to North-Island natural-gas import processes. They are outside the valid process-region domain and do not enter the objective. |
| South-Island geothermal data | xl2times retains 16 North-Island geothermal processes in SI, with associated `RTP`, cost, life, and availability records. Each is also in `NO_ACT`, so it cannot operate. |
| Agricultural electrification and hydrogen `PRC_ACTFLO` | xl2times has 648 activity-to-flow records (27 processes, two regions, and their model years) absent from the VEDA-preprocessed GDX. This is a real topology difference, not merely a label difference. However, each corresponding process has zero `VAR_Act` in the generated Steady solution; only `VAR_ActM` marginal records are reported. It therefore does not explain this result unless the mapping changes another active equation indirectly. |
| Other process-domain records | The remaining `PRC_CAP`, `NCAP_COST`, `NCAP_ELIFE`, `NCAP_AFA`, and related differences follow the same pattern: records for processes or regions that are not selected/valid in the Steady solution. |
| `COM_PROJ` | Most differences are explicit xl2times values in non-milestone years where VEDA relies on internal interpolation. They do not directly change the milestone-period optimisation inputs. |

This narrows the evidence. The GDXs are still not identical, and the
`PRC_ACTFLO` topology difference belongs in the compatibility inventory, but
none of the identified residuals has yet been shown to change an active
Steady decision, objective coefficient, or binding constraint.

### End-of-time check

The generated model was also rebuilt with the legacy 2200 end-of-time
behaviour. The only semantic DD changes were removal of two zero-valued
`PRC_RESID` records in 2223 and removal of `DATAYEAR(2223)`. The solve
objective was unchanged at 1,469,035.4824 MioNZ$. The horizon difference is
therefore not the explanation for the current objective gap.

### Full generated-matrix comparison

Both 2200-horizon cases were exported through GAMS CONVERT, which produces a
named sparse matrix after TIMES has assembled the LP. The diagnostic artifacts
are retained below `build/solves/`: the xl2times export is
`steady-20261028T183334Z/diagnostics/`, and the isolated VEDA export is
`steady-v309xl2times-test-veda-diagnostic/diagnostics/`.

The `WEM` and `WEM_SI` constraint rows match exactly after normalising
non-semantic differences in GAMS rendering (case and quoting of labels): all
27 rows have the same named variables and coefficients, for 4,332 non-zero
entries on each side. The different final binding statuses of those constraints
are therefore downstream effects, not a difference in their definitions.

The complete matrices nevertheless have a material structural difference:

| Matrix item | xl2times | VEDA |
| --- | ---: | ---: |
| Named equations | 605,276 | 620,732 |
| Named variables | 499,238 | 514,470 |
| Dumped non-zero matrix entries | 3,307,522 | 3,209,932 |

The named set difference is highly concentrated rather than diffuse:

- VEDA has 15,552 additional `EQ_ACTFLO` equations, with a paired 15,552
  additional `VAR_FLO` variables. The first examples are time-sliced
  `ADCF-MOTP-MOB-BIKE-ELC` flows in 2025; this family needs to be traced to
  its process-flow and activity-flow input handling.
- xl2times has 96 additional `EQL_CAPACT` equations and 96 paired
  `VAR_NCAP` variables, plus 224 additional `VAR_FLO` variables for
  South-Island geothermal `ELCCO2` flows. These align with previously known
  inactive/out-of-domain representation differences.

The VEDA-only activity-flow family is now the strongest structural lead. It
should be checked before interpreting any later-year WEM, technology-cap, or
fuel-use binding difference as a root cause.

### `EQ_ACTFLO`: demand-process activity-unit mismatch

The VEDA-only `EQ_ACTFLO` family has now been traced.  It is not a broad
matrix-generation discrepancy: it consists of exactly 27 `DMD` technologies
from `SubRES_NewTechs_AGR_Steady.xlsx`, in both regions, for the 12 model
years 2025--2050 and all 24 DAYNITE time-slices:

```
27 processes × 2 regions × 12 years × 24 time-slices = 15,552 equations
```

The processes are agricultural mobile plant technologies (electric and
hydrogen variants), plus `AINDC-SH-Boiler-ELC` and
`AINDC-SH-Boiler-H2R`.  Examples include
`ADCF-MoTP-Mob-Bike-ELC`, `AHORT-MoTP-Mob-Trac-H2R`, and
`AFORE-MoTP-Mob-GB-ELC`.

This is an activity-unit construction difference.  The source `~FI_T` rows
contain an energy input and a broad demand output; for example,
`ADCF-MoTP-Mob-Bike-ELC` specifies `AGRELC` as `Comm-In` and
`ADCF-MoTP-Mob` as `Comm-Out`.  VEDA's DD generator applies its demand-process
conventions and assigns the more specific demand commodity
`ADCF-Bike-MoTP-Mob` as the `PRC_ACTUNT` commodity.  Its `TOP` entry still
lists only the energy input.  Thus the demand-side activity commodity is an
implicit VEDA construct, rather than a literal `TOP` output or a direct copy
of `Comm-Out`.

xl2times instead assigns the energy input's primary commodity group:

| Process | VEDA `PRC_ACTUNT` commodity | xl2times `PRC_ACTUNT` commodity |
| --- | --- | --- |
| `ADCF-MoTP-Mob-Bike-ELC` | `ADCF-Bike-MoTP-Mob` | `AGRELC` |
| `AINDC-SH-Boiler-ELC` | `AINDC-Boiler-SH` | `AGRELC` |
| `AINDC-SH-Boiler-H2R` | `AINDC-Boiler-SH` | `AGRH2R` |

The same pattern holds for all 27 processes.  Consequently the VEDA matrix
contains the demand-side `EQ_ACTFLO` / `VAR_FLO` pairs, while the generated
matrix does not.  This corrects the earlier shorthand that the difference was
an inverted `Comm-In`/`Comm-Out` mapping: the relevant VEDA commodity is
derived from VEDA's `DMD` convention, not copied from either cell.

This is a material compatibility defect, but is unlikely to explain the
current Steady objective gap directly.  None of the 27 processes has a
non-zero `VAR_Act` result in either completed Steady solve.  Their missing
equations therefore do not contribute activity, fuel use, emissions, or cost
at the observed optimum.  They must nevertheless be fixed before treating
xl2times as equivalent: they can become active in another scenario or after
an otherwise small model change.

The earlier preprocessed-GDX observation that xl2times contains extra
`PRC_ACTFLO` *parameter* records is not contradictory.  `PRC_ACTFLO` is an
input/preprocessing representation, whereas `EQ_ACTFLO` and `VAR_FLO` are
the final LP equation and variable families.  The decisive difference here is
the primary activity commodity used when TIMES assembles the LP.

### Earliest active divergence

To find a causal lead rather than rank later effects, `VAR_Act` records were
first aggregated by process, region, and period (discarding the time-slice
coordinate only for this screening exercise).  The first-period result is
not a substantive technology-choice divergence: in 2023, the only unequal
aggregate is North-Island `ELC_BAT_2H` activity.  Both runs have the same
0.035 existing capacity and no 2023 new capacity for that battery.  All 24
of its time-slice activity-variable columns have identical final-LP
coefficients in the two diagnostic matrices.  The different battery dispatch
is consequently a downstream dispatch/degeneracy symptom, not evidence that
the battery's own input data were converted differently.

The first material investment divergence occurs in 2024, in North-Island
passenger transport:

| New capacity in 2024 | xl2times | VEDA | Difference |
| --- | ---: | ---: | ---: |
| `T_P_CBEVELC_HIGH` | 28.930 | 20.408 | +8.522 |
| `T_P_CHYBPET_HIGH` | 23.525 | 32.539 | -9.014 |

This is a substitution—more high-range BEV capacity and less high-range
petrol-hybrid capacity in xl2times—not yet its cause.  The diagnostic matrix
gives a useful negative result: for each of these two 2024 `VAR_NCAP`
variables, all 26 non-zero coefficients are identical between the matrices,
including their investment and fixed objective coefficients, capacity
equations through their lifetime, and capacity-to-activity terms.  Their own
cost, life, and capacity construction are therefore not the discrepancy.

The adjacent 2024 activity shifts include coal supply moving from NI in VEDA
to SI in xl2times and small changes in electricity transfer, diesel, petrol,
and residential heat activity.  These are better treated as candidate
upstream balance/topology differences than as proven causes.  The next
targeted comparison should therefore examine the common 2024 commodity
balance equations and their right-hand-side requirements for the commodities
connected to these shifts; a variable-column comparison alone cannot reveal
a differing equation RHS or an equation that is absent in one matrix.

### North-Island electricity peak-demand RHS difference

The CONVERT matrix alone contains coefficients, but not equation right-hand
sides or bounds.  A subsequent diagnostic export retained the sparse matrix,
dictionary, and CPLEX-LP representation for each formulation.  The LP files
are retained at:

- `build/solves/steady-rhs-diagnostic-xl/diagnostics/diagnostic-model.lp`
- `build/solves/steady-v309xl2times-rhs-diagnostic/diagnostics/diagnostic-model.lp`

This rules out the initial transport hypothesis.  The 24 time-slice RHS values
for North-Island 2024 `T_P_CAR` commodity balances are identical.  The
`TRAELC` electricity and `TRAPET` petrol commodity-balance RHS values are also
identical (zero in both formulations).  The 2024 BEV and petrol-hybrid
activity-variable columns are identical as well.

After normalising equation labels and ignoring numerical differences below
`1e-10`, the LP comparison identifies 312 material RHS differences.  Every
one is a North-Island electricity `EQ_PEAK` constraint: 13 model periods
(2024--2032, 2035, 2040, 2045, and 2050) times 24 time-slices.  For example:

| Constraint | xl2times RHS | VEDA RHS |
| --- | ---: | ---: |
| NI 2024 `EQ_PEAK(ELC, FAL-WK-D)` | -12.5785494802 | -12.0892039076 |
| NI 2024 `EQ_PEAK(ELC, SUM-WK-D)` | -12.0067972311 | -11.5396946391 |

`EQ_PEAK` requires peak-capable electricity supply to meet consumption.  The
CPLEX-LP RHS is a *net residual*: GAMS has moved all constant terms out of the
equation, including projected/fixed peak consumption and supply from existing
capacity.  It is not a literal demand quantity.  Thus the more-negative
generated RHS means that, holding the displayed variable terms fixed, the
generated equation has a 0.4893455726 lower residual requirement in this
example.  It can result from lower peak demand, greater fixed peak supply,
lower fixed peak consumption, or a combination of those effects.  This is a
proven effective-model difference, not evidence of a different fixed
electricity price.  Electricity's marginal cost remains endogenous, but this
constraint can change generation and network choices and consequently affect
that cost.

`COM_PROJ` has also been tested at the effective-model level.  Of 195,444
shared LP equation RHS values, the only material differences are the 312
`EQ_PEAK` rows above.  In particular, all shared `EQG_COMBAL` RHS values
match within `1e-10`; the 821 textual numeric differences in that family are
floating-point noise below that threshold.  Because `EQG_COMBAL` applies the
per-commodity projected demand and its time-slice allocation, this rules out
a material difference in the effective ordinary commodity demand for any
common NI commodity—not merely `T_P_CAR`.

That does not prove that every intermediate `COM_PROJ` record is rendered the
same way, nor does it rule out peak-specific aggregation or fixed supply.
`EQ_PEAK` sums the same demand commodities through peak-group mappings and
applies additional peak factors, while existing capacity can contribute a
constant supply term.  The remaining cause must therefore be in that
aggregation, a peak-specific factor, or a fixed supply/consumption term,
rather than in a normal commodity-balance demand requirement.

#### Peak-demand investigation checklist

##### Peak-row existence and variable membership

This component has now been checked at the final-LP level:

| Check | Result |
| --- | --- |
| Named `EQ_PEAK` rows | Exact match: 672 rows in each LP. This includes 336 NI `ELC` rows (14 periods × 24 time-slices). |
| Raw `COM_PEAK` input | Exact match: NI `ELC` and SI `ELC`. |
| Raw `COM_TSL` input | Exact match: 484 records in each input after normalising VEDA's unquoted `.DAYNITE` syntax. |
| Variables in peak rows | Different in 576 rows. NI differs for the 312 rows from 2024--2050; SI differs for 264 rows from 2026--2050. |

For example, the generated NI 2024 peak rows include `VAR_NCAP` terms for
`ELC_GEO_TAUHARASTAGE1`, `ELC_GEO_TEHUKAUNIT3`, and
`ELC_WINDON_HARAPAKIWINDFARM`; the corresponding VEDA rows include the
time-sliced `VAR_ACT` terms for those technologies.  This is a real
peak-equation construction difference, consistent with the wider
activity-flow compatibility differences already recorded above.

It is not, however, a direct explanation of the residual RHS difference:
the same kind of variable-membership difference occurs in the 264 South-
Island rows, whose RHS values match.  It must be retained as a compatibility
issue and compared when assessing the full peak constraints, but the
NI-only constant residual must arise from a separate fixed term or
peak-specific demand factor.

The residual is assembled as:

```text
fixed peak consumption + exogenous projected peak demand - fixed peak supply
```

The following is the complete working list for the input comparison.  The
items are ordered so that a difference can be isolated before looking at
downstream decisions.  “Fixed” means a term that remains constant before the
LP is solved; new capacity, dispatch, trade, and flexible demand are variable
LP terms and are deliberately excluded.

| Component | Inputs to compare | How it enters the residual | Current status |
| --- | --- | --- | --- |
| Peak-row existence and membership | `COM_PKTS`, `COM_GMAP`, `COM_TS` | Selects the peak group, member commodities, and time slices represented by the row. | Row existence and `COM_TSL` are matched; member-level `COM_GMAP` construction is not yet reconciled. |
| Exogenous projected demand | `COM_PROJ`, commodity demand membership (`DEM`) | Supplies the constant demand quantity. | Ordinary `EQG_COMBAL` RHS values match materially; this strongly rules out a normal per-commodity demand difference. |
| Demand time-slice allocation | `COM_FR`, `RS_FR` | Allocates projected demand to the represented slice. | Ruled out: both effective parameters match exactly after normalising VEDA's mixed-case labels (`COM_FR`: 241,682 records; `RS_FR`: 442). All 481 NI-ELC `COM_FR` records for 2024--2050 match. |
| Peak demand adjustment | `COM_PKFLX` | Applies the peak-flexibility multiplier to projected demand. | Ruled out: the effective preprocessed parameter is empty in both cases. |
| Fixed capacity-related consumption | Existing stock/capacity data (`PRC_RESID`, `PRC_CAP`, `NCAP_PASTI`) and their electricity-flow/peak coefficients, including `FLO_PKCOI` where applicable | Adds constant electricity consumption associated with existing capacity or fixed flows. | Ruled out. `FLO_PKCOI` matches exactly (2,428 records; all 73 NI-2024-ELC records are `1`); `NCAP_PASTI` also matches exactly (1,031 records). The capacity-consumption route is empty in both models: `NCAP_COM`, `COEF_CIO`, and `COEF_ICOM` have no effective records. |
| Fixed peak-capable supply | `NCAP_PASTI`, capacity-activity and flow coefficients (`PRC_CAPACT`, `PRC_ACTFLO`, `NCAP_PKCNT`, `COEF_VNT`), plus `COM_IE`, `RS_FR`, and reserve factor `COM_PKRSV` | Subtracts the usable contribution of existing supply capacity from the residual. | **Root cause identified.** All numeric inputs match, but xl2times has extra derived `RPC_PKC` membership for six existing NI generators with non-zero peak contribution. It consequently subtracts additional fixed supply, producing the lower (more negative) `EQ_PEAK` RHS. |
| Fixed demand-model additions | Demand elasticity, aggregation, shares, and demand-flex inputs (`RD_NLP`, `RD_AGG`, `RD_SHAR`, and associated data) | Can add a constant demand-side term when the relevant feature is active. | Applicability to NI `ELC` peak rows not checked. |

The systematic comparison order is therefore:

1. Confirm member commodities and slices through `COM_GMAP`, `COM_TS`, and
   `COM_PKTS`.
2. Treat `COM_PROJ` as provisionally ruled out at the effective commodity
   balance level; verify only if the peak membership check selects a commodity
   without a comparable ordinary balance row.
3. `COM_FR`, `RS_FR`, and `COM_PKFLX` are ruled out: the first two match
   exactly and the latter has no effective records in either input.
4. Fixed capacity-related consumption is ruled out: there are no effective
   capacity-consumption records, and ordinary flows, trade, storage, and
   blending remain LP variables rather than fixed RHS terms.
5. Fixed existing peak supply explains the full NI `EQ_PEAK` RHS difference;
   correct the activity-unit construction that causes the derived peak-capacity
   membership mismatch.
6. Check demand-model additions only where they are active if a residual
   remains after that correction.
7. Reconstruct each side's residual from the isolated components. If all
   components agree, trace the TIMES preprocessor/DDL update sequence; only
   then investigate an assembly convention difference.

##### Fixed peak-capable supply: identified cause

The fixed-supply term in `eqpeak.mod` credits existing capacity through
`NCAP_PASTI` only where the derived set `RPC_PKC(REG,PRC,COM)` identifies the
process as contributing to peak capacity.  Every numeric input to that term
matches after label normalisation: `NCAP_PASTI` (1,031 records),
`PRC_CAPACT`, `PRC_ACTFLO`, `NCAP_PKCNT`, `COEF_VNT`, `G_YRFR`, `COM_IE`, and
`COM_PKRSV`.

The derived membership does not match. xl2times has 271 `RPC_PKC` records and
VEDA has 87; all VEDA records occur in xl2times, with 184 additional generated
records. Seven additional NI electricity generators have existing capacity:

| Process | Existing capacity vintage | Capacity | Effective peak contribution |
| --- | ---: | ---: | --- |
| `ELC_GEO_KAWERAUTOPP2` | 2025 | 0.049 | Yes |
| `ELC_GEO_TAUHARASTAGE1` | 2024 | 0.152 | Yes |
| `ELC_GEO_TEHUKAUNIT3` | 2024 | 0.0514 | Yes |
| `ELC_GEO_TEMIHIEXPANSION` | 2027 | 0.180 | Yes |
| `ELC_SOLARTRACK_TWINRIVERSSOLARFARM` | 2024 | 0.024 | No: its peak-capacity factor is zero |
| `ELC_WINDON_HARAPAKIWINDFARM` | 2024 | 0.176 | Yes |
| `ELC_WINDON_KAIWAIKAWE` | 2026 | 0.073 | Yes |

Reconstructing the exact `eqpeak.mod` fixed-supply expression produces an
additional xl2times supply contribution for every one of the 312 NI `ELC`
rows whose RHS differs. For example, in 2024 `FAL-WK-D`, it is
`0.489345572571`, exactly the magnitude of the known RHS difference
(`-12.5785494802` xl2times versus `-12.0892039076` VEDA). The sign is as
expected: extra fixed supply on the left-hand side is moved to the right by
GAMS Convert, making the generated RHS more negative.

The upstream construction difference is `PRC_ACTUNT`. For each of those
generators, xl2times assigns `ELC` as the activity commodity, while VEDA
assigns a process-specific `*_NRGO` commodity (for example,
`ELC_GEO_TAUHARASTAGE1_NRGO`). TIMES therefore derives different `RPC_PKC`
membership even though the installed capacity, activity-to-flow conversion,
and peak-capacity factors agree. This is the compatibility defect to correct;
changing the peak coefficients or trimming capacity data would treat the
symptom rather than reproduce VEDA's model construction.

Generation costs, capacity choices, WEM/WEM_SI binding status, inter-island
transfers, fuel use, and emissions are deliberately excluded from this list.
They are downstream responses to the peak constraint and cannot establish why
its RHS differs.

## Next investigation steps

### Compare binding equations in the final model

The next investigation should compare final-equation levels, slacks, and
marginals from the two completed GAMS runs, ranking cases where one run is
binding and the other is not, or where their shadow prices differ materially.
The initial focus should be national/region emissions constraints, commodity
balances, and user constraints associated with the divergent electric-
transport and fuel choices.

This is more useful than further unfiltered DD or GDX comparison. The raw
post-preprocessing differences now identified are predominantly inactive or
out-of-domain. In contrast, a missing, relaxed, or differently assembled
*effective* constraint will be visible directly as a difference in whether
the corresponding final equation binds and in its marginal value. That gives
a specific equation and process/commodity/year to trace back through the
preprocessed GDX, DD records, workbook, and—if necessary—the xl2times
transform.

The comparison should use stable equation coordinates rather than the order
in which GAMS emits records. It should first establish whether the lower
xl2times cost and emissions come from a differently binding constraint or a
different but feasible near-optimal technology mix. Only then should we make
a targeted compatibility change or investigate DD update order.

### Initial final-equation findings

This comparison has now been run using the final solution GDX files produced
with the same 2250 end-of-time setting. It does **not** show a missing carbon
or imported-fuel price signal:

- the `EQE_COMBAL` marginal records for `TOTCO2` are identical for every
  region and model year;
- the `EQG_COMBAL` marginal records for `DSL`, `PET`, and `LNG` are likewise
  identical for every common region and model year.

This corroborates the earlier DD comparison: the carbon-tax and imported-fuel
price inputs are reaching the final generated model equivalently. The lower
fuel costs in the xl2times result are therefore caused by lower fuel use, not
by a lower effective price.

The user constraints are present and active in both models. Their shadow
prices differ because the overall solutions differ. The notable changes in
binding status are:

- `WEM_SI` is binding in both models in 2024, 2025, and 2027, but is binding
  only in xl2times in 2032 (marginal 0.732 versus zero in VEDA);
- the national `WEM` constraint is binding in both models for most years, but
  is binding only in VEDA in 2040 (marginal 295 versus zero in xl2times);
- several technology-growth constraints bind in only one model, including
  passenger BEVs, residential gas/LPG technologies, distributed BESS, and
  some commercial technology limits;
- two coal-ban constraints are binding only in VEDA: `COAL-BAN-MINE-SH_LOW`
  in 2040 and `COAL-BAN-FOOD-BOILR-PH_LOW` in 2045.

These are consequences and useful trace points, rather than evidence that
the respective constraints were omitted: their RHS and coefficient inputs
already match. The next targeted investigation should trace the first
technology-choice divergence before 2024--25, concentrating on the
process-flow topology and effective coefficients for technologies appearing
in the one-sided binding constraints. That is now a stronger lead than
carbon, fuel pricing, or the WEM input itself.

### Solver-settings check

The aligned 2250 runs use the same solver configuration: GAMS 44.4 with
CPLEX 22.1.1, `LP=cplex`, `RESLIM=50000`, `ITERLIM=999999`, `REDUCE=YES`,
`VAR_UC=YES`, and no `cplex.opt` file in either run directory. Both terminate
with GAMS solver status 1 (normal completion), model status 1 (optimal), and
the CPLEX message `Optimal solution found`.

The lower xl2times objective is therefore not CPLEX finding a better solution
to the same LP. For one fixed LP, an LP solver's proven optimal objective
would be the same apart from numerical tolerance, not about 1,415 MioNZ$.
It is the optimum of a differently assembled LP. The remaining candidate
causes are consequently effective model structure or coefficients (including
process-flow topology and DD update effects), not solver settings.
