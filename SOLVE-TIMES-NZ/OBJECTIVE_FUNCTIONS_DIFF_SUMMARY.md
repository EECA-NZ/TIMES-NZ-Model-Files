# Objective-function difference summary

## Purpose and outcome

This work aimed to make the TOML/xl2times build reproduce the existing VEDA
Steady case, then to distinguish genuine conversion defects from harmless
differences in representation or alternative LP solutions.

The final comparable Steady runs are extremely close:

| Run | Objective (`ObjZ`, MioNZ$) | Difference from VEDA |
| --- | ---: | ---: |
| VEDA reference | 1,470,450.003441 | 0 |
| TOML/xl2times | 1,470,449.765529 | -0.237912 (-0.0000162%) |

The remaining agricultural demand-process activity-unit mismatch was also
tested after this result. Adding VEDA's 27 missing demand-service PCGs gave
an objective of 1,470,449.766200 MioNZ$: only +0.000671 MioNZ$ different.
That compatibility correction does not explain the residual gap.

Currently remaining things to solve: 

- ag demand processes in steady subres are mis-specified, flagging commodities that don't exist. fix. 
- decide the intended post-VEDA PCG/peak-credit design;
- move the five biofuel conversions into SubRES, then remove the temporary VEDA cost-omission workaround.


## Compatibility wrapper inventory

`src/solve_times_nz/xl2times_compat.py` is deliberately a small
project-owned wrapper around xl2times 0.3.0. Its hooks fall into three
categories below. Each needs a focused regression test while it remains.

### Keep: corrections to the conversion or project interface

These handle valid TIMES-NZ inputs or preserve model information that the
converter would otherwise lose. They should be retained, ideally moved
upstream into xl2times once stable.

| Wrapper behaviour | Why it is needed | Long-term direction |
| --- | --- | --- |
| Add missing optional process/commodity `description` columns | Not really necessary but matches Veda behaviour, making comparisons easier. | Upstream robustness fix. |
| Permit a demand driver to reach and remain at zero, while rejecting a `0 -> non-zero` restart | A continuing zero demand is valid; dividing by the prior zero otherwise corrupts projection. A restart is ambiguous and is correctly rejected. | Upstream demand-projection fix. |
| Expand a generic `UC_FLO` across a declared multi-region `R_E`/`R_S` set | The source constraint declares its intended regions before xl2times has fully assembled the model region set. | Upstream user-constraint handling fix. |
| Export implied environmental topology (`FLO_EMIS`) into `TOP` | The implied emissions links are required model topology and must reach TIMES. Veda does this automatically but xl2TIMES does not use inferred topology when defining TOP | Upstream dictionary-export fix. |
| Write DD values at 15 significant digits | This matches observed VEDA DD precision and prevents avoidable coefficient drift from upstream's shorter serialisation. | Retain as the project serialisation policy unless xl2times offers an equivalent configured precision. |
| Keep the xl2times compatibility log in the build output directory | A build artefact belongs with its generated DD files, rather than polluting the repository working directory. | Keep as build hygiene; it has no mathematical effect. |
| Suppress generated zero `PRC_RESID` rows beyond the active legacy year domain | A derived stock-expiry record outside `EOTIME` is not a valid member of the solve's year domain. Source residual data and lifetimes are retained. | Replace the fixed `2200` constant with an upstream/domain-aware implementation if different horizons become routine. |

### Retain only while reproducing the legacy VEDA formulation

This is not a VEDA data error, but it is an inherited formulation convention.
It must remain while objective matching against the reference VEDA model is a
requirement. It is not necessarily the desired formulation for a future,
deliberately redesigned model.

| Wrapper behaviour | Observed effect | Decision needed before replacing it |
| --- | --- | --- |
| Assign `NRGO` as the primary commodity group to every Supplemental Resource process with an energy (`NRG`) output and no explicit PCG | Reproduces all 213 VEDA `*_NRGO` activity-unit pairs. Before this, xl2times generated only 12, leaving 528 `EQ_PEAK` rows to use capacity where VEDA used time-slice activity. Matching the groups removed those active peak-row differences and closed 96% of the original objective gap. | Define the intended peak-credit method independently of VEDA. The likely future approach is to give electricity-*generating* processes an explicit `ELC` PCG, with a clearly defined scope that excludes storage, networks, trade, and demand-side processes as appropriate. Treat that as a documented model-method change and revalidate peak equations. |
| Assign VEDA's demand-service PCG to 27 agricultural `DMD` processes | Reproduces the missing 15,552 `EQ_ACTFLO` equations. The Steady objective changed by only +0.000671 MioNZ$, confirming this inactive family does not explain the remaining gap. | Replace the explicit mapping with a tested, general xl2times implementation of the demand-process convention. Do not extend it from process-name similarity alone. |

`NRGO` is an internal activity-unit group, not an extra energy commodity or a
workbook input. In the legacy formulation it changes which TIMES peak
construction is used. The compatibility rule therefore reproduces VEDA; it
does not endorse VEDA's use of time-slice activity as the intended definition
of dependable capacity credit.

### Remove: temporary emulation of a VEDA error

This exception exists only to reproduce an erroneous legacy VEDA export. It
must be deleted once the affected technologies are represented correctly.

| Temporary wrapper behaviour | VEDA error reproduced | Proper replacement |
| --- | --- | --- |
| Drop `NCAP_COST` for `CT_COILBDS`, `CT_CWODBPL`, `CT_CWODDID`, `CT_CWODETH`, and `WSTWOD2WOD` | The base-workbook `Biofuels` `~FI_T` rows supply `INVCOST`, but VEDA omits the corresponding `NCAP_COST` records. It consequently treats future conversion technologies as unconstrained activities rather than capacity investments. | Move the technologies to the appropriate SubRES/new-technology pathway, retain their capital costs and capacity formulation, remove this named exception, and accept/rebaseline the deliberate model-result change. |

This one temporary exception explained the final material gap after NRGO
matching: the objective moved from +54.092781 to -0.237912 MioNZ$ when the
five costs were omitted. It is deliberately narrow; it is not a rule that
future-starting processes should be free. Veda expected future technologies to be expressed in subres files, so this could also be resolved by splitting some base year files. 
