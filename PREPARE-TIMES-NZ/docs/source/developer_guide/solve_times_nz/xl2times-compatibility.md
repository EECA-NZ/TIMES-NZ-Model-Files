# xl2times compatibility

`SOLVE-TIMES-NZ` uses `xl2times==0.3.0` with `pandas<3`. The pandas upper bound
is required because this xl2times release is not compatible with pandas 3's
Arrow-backed string behaviour.

The build command runs the project-owned `xl2times-fixed` entry point rather
than modifying the installed xl2times package. Its implementation is
`SOLVE-TIMES-NZ/src/solve_times_nz/xl2times_compat.py`; focused regression
tests are in `SOLVE-TIMES-NZ/tests/test_xl2times_compat.py`.

## Why a wrapper exists

The wrapper preserves valid TIMES-NZ information that xl2times 0.3.0 otherwise
loses or cannot process, while keeping corrections to malformed or ambiguous
model data in `PREPARE-TIMES-NZ`. It patches the converter only at runtime and
does not alter source workbooks or installed Python files.

The current wrapper:

- accepts omitted optional process and commodity descriptions;
- permits a demand driver to continue from zero to zero, while rejecting an
  ambiguous zero-to-non-zero restart;
- expands generic `UC_FLO` terms over declared multi-region `R_E` or `R_S`
  user-constraint sets;
- exports implied environmental `FLO_EMIS` topology to the TIMES `TOP` table;
- writes non-integer floating-point DD values at 15 significant digits;
- omits only generated zero `PRC_RESID` rows beyond the established 2200 VEDA
  time domain; and
- writes the xl2times log beside the generated DD output rather than in the
  caller's working directory.

## Maintenance rules

Prefer an upstream fix in xl2times when it is broadly valid. Prefer a
`PREPARE-TIMES-NZ` correction when an input is malformed, incomplete, or relies
on implicit VEDA behaviour. Add or retain a wrapper change only when valid
TIMES-NZ input cannot be represented correctly by the pinned converter.

Every wrapper change must have a focused regression test. Do not patch files
inside the installed xl2times package: those edits are machine-local, vanish
when dependencies are refreshed, and cannot be reproduced by another modeller.

## Compatibility decision register

| Behaviour | Reason | Regression coverage |
| --- | --- | --- |
| Add omitted optional process and commodity `description` columns | xl2times wildcard handling selects this optional field unconditionally. | Optional-description test |
| Permit a demand driver to remain at zero, but reject a zero-to-non-zero restart | `0 / 0` is a valid continuation; a restart has no defined percentage change. | Zero-continuation and restart-rejection tests |
| Expand generic `UC_FLO` across a declared `R_E` or `R_S` multi-region set | User constraints are processed before xl2times has assembled the complete region set. | Multi-region `UC_FLO` test |
| Export implied environmental `FLO_EMIS` links to `TOP` | Derived emission topology is required by TIMES but is not exported by xl2times 0.3.0. | Implied-environmental-topology test |
| Use 15 significant digits for non-integer DD values | This preserves the precision used by the VEDA reference DD files. | VEDA-precision test |
| Omit generated zero `PRC_RESID` rows after 2200 | The established VEDA run has a 2200 end-year domain; explicit source rows and lifetimes remain untouched. | Legacy-horizon residual test |
| Write the converter log in the requested DD output directory | A build artefact belongs with the generated case rather than the caller's working directory. | Output-directory argument test |

## Upstream input rules

These are model-input requirements, not wrapper exceptions. Keep the relevant
PREPARE-TIMES-NZ tests and generated-workbook checks when changing the writer.

| Input area | Required convention |
| --- | --- |
| Trade links | Worksheet names begin with `uni_` or `bi_`; the full words are not recognised by the converter. |
| User constraints | Put `~UC_Sets` declarations above `~UC_T`; leave the cell immediately right of `~UC_T` blank and put headers on the next row. |
| Numeric values | Emit demand `COM_PROJ`, singleton `~StartYear`, and process lifetime cells as numeric Excel values, not numeric-looking strings. |
| Transform availability | Use a `Value` column for all-region `~TFM_AVA` values; `AllRegions` is not accepted in this converter path. |
| Commercial boiler topology | `Comm-Out` must use the declared heat-demand commodity, not a technology-specific undeclared name. |

## Known non-fatal converter warnings

The following warnings were observed with xl2times 0.3.0 and did not block the
current conversion. Reassess them when upgrading xl2times or changing the
affected workbook families:

- Tags missing from bundled `veda-tags.json`, including `tfm_ava_c`,
  `tfm_fill_r`, `time_slices`, `tradelinks`, and `uc_sets`.
- The unrecognised `~IMPSETTINGS` table is dropped.
- Missing column-alias entries for `~TRADELINKS`, `~STARTYEAR`,
  `~ACTIVEPDEF`, `~TIMEPERIODS`, `~CURRENCIES`, `~DEFUNITS`, and
  `~TIMESLICES`.
- Region specifications in the LNG import worksheets are reset because that
  dimension is unsupported there.
- A pandas `DataFrameGroupBy.apply` future-deprecation warning from
  `include_cgs_in_topology`.

When a warning changes, treat it as a compatibility review: reproduce it with
the smallest suitable case, decide whether it is an upstream, PREPARE, or
wrapper concern, add a focused regression test where appropriate, and update
this page.
