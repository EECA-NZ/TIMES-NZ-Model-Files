# xl2times issue log

This file tracks compatibility problems and model-layout issues encountered while
converting `models/TIMES-NZ` with xl2times 0.3.0.

The current test command is:

```bash
uv run xl2times-fixed "models/TIMES-NZ" --ground_truth_dir=ground_truth -v
```

The current command completed successfully on 22 October 2026, producing 79
tables and 99,410 rows. It passed both `process_transform_availability()` and
`apply_final_fixup()`.

## How the compatibility wrapper works

`solve_times_nz.xl2times_compat` is a small, project-local entry point
implemented in `src/solve_times_nz/xl2times_compat.py`. It imports the
installed xl2times functions, retains references to the original functions,
then replaces five transform hooks and redirects its log immediately before
invoking the ordinary xl2times CLI. It does not edit
the installed package or alter Excel inputs.

The hooks and log configuration run at these points:

1. `generate_topology_dictionary`: inserts a blank `description` column into
   process and commodity dataframes when an optional description was omitted.
   This prevents the wildcard transform from selecting a non-existent column.
2. `_project_demands`: permits a demand driver to stay at zero by treating only
   `0 → 0` as a ratio of one. It preserves the ordinary calculation otherwise
   and raises an error for an unsupported `0 → non-zero` restart.
3. `process_user_constraint_tables`: temporarily makes declared `R_E`/`R_S`
   regions visible while xl2times processes a `~UC_T` table, restores the
   original model-region set afterwards, explodes explicit comma-separated
   region results, and replicates only an unqualified `UC_FLO` column when a
   table has exactly one declared region set. Explicitly regional UC columns
   are left unchanged.
4. `complete_dictionary`: appends `model.implied_topology` to the exported
   `Topology` dictionary, deduplicated on region, process, commodity, and
   direction. xl2times derives this topology for ENV-targeted `FLO_EMIS`; the
   hook makes it reach the TIMES `TOP` table without changing the model's
   physical topology during transformation.
5. `convert_to_string`: formats non-integer floating-point values with 15
   significant digits rather than xl2times' upstream 10. VEDA DD output uses
   up to 15 significant digits; retaining that precision prevents avoidable
   numerical perturbations in a tightly constrained model.
6. `setup_logger`: directs the xl2times log to the requested `--output_dir`,
   alongside the generated DD files, rather than the directory from which the
   command was invoked.

The wrapper deliberately does not correct input-data region expansion,
commodity-group generation, or process naming. Those remain PREPARE-TIMES-NZ
responsibilities and are tracked in the current difference inventory.

### Patch policy

All temporary or model-specific xl2times compatibility changes belong in
`src/solve_times_nz/xl2times_compat.py`, with a regression test in
`tests/test_xl2times_compat.py` and an entry in this file. Do not patch files
in the installed `xl2times` package: those changes are machine-local, are lost
when `uv sync` refreshes the environment, and cannot be reproduced by another
modeller. Prefer correcting malformed or ambiguous source data in
PREPARE-TIMES-NZ; add a wrapper hook only when the input is valid but xl2times
cannot represent the established TIMES/ VEDA behaviour.

## Resolved by project configuration

### Pandas 3 fails while processing user constraints

**Symptom**

```text
ArrowNotImplementedError: Function 'binary_join_element_wise' has no kernel
matching input types (null, large_string, large_string)
TypeError: operation 'radd' not supported for dtype 'str' with dtype 'object'
```

The failure occurred in `_custom_melt()` while xl2times concatenated nullable
attribute values.

**Cause**

xl2times 0.3.0 declares `pandas>=2.1` without an upper bound, so uv originally
selected pandas 3.0.5. The xl2times string-processing code is not compatible
with the Arrow-backed string behaviour encountered in that version.

**Resolution**

The project now declares `pandas<3`. After relocking and syncing, uv selected
pandas 2.3.3. This allowed `process_user_constraint_tables` to complete.

**Status:** Resolved by dependency constraint.

## Resolved by updating PREPARE-TIMES-NZ

### Trade-link worksheet names were not recognized

**Symptom**

```text
KeyError: 'regions'
```

The failure occurred in `harmonise_tradelinks()`.

**Cause**

The worksheets were named `Unilateral` and `Bilateral`. xl2times checks the
first underscore-separated part of each sheet name for the exact value `uni`
or `bi`. The full words therefore entered an invalid fallback code path that
used `regions` before creating it.

**Resolution**

Rename the sheets so their names are `uni` and `bi`, or begin with `uni_` and
`bi_`.

**Status:** Resolved in PREPARE-TIMES-NZ by worksheet renaming.

### `~UC_Sets` beside `~UC_T` hid the real UC tables

**Symptom**

```text
KeyError: 'uc_n'
```

The affected worksheets were:

- `VehicleUtilisation`
- `CapacityLimits`
- `CoalBan`
- `UC_WEM`
- `UC_WEM_SI`

**Cause**

The original layout placed `~UC_T` in `A3` and a `~UC_Sets` declaration in
`B3`. xl2times treats a populated cell immediately to the right of a table tag
as that tag's scalar value. It consequently extracted a one-cell `~UC_T` table
instead of the data table beginning with `UC_N` on the following row.

**Resolution**

Move every `~UC_Sets` declaration above `~UC_T`, leave the cell immediately to
the right of `~UC_T` blank, and leave the UC headers immediately below it. For
example:

```text
A2: ~UC_Sets: R_S: AllRegions
B2: ~UC_Sets: T_S:
A3: ~UC_T
B3: [blank]
A4: UC_N
```

The sets remain attached to the extracted UC table because xl2times accumulates
them before encountering the table tag.


**Status:** Resolved in PREPARE-TIMES-NZ by worksheet layout changes.
`generate_uc_properties` and UC wildcard expansion complete in the current run.

### Base-year `COM_PROJ` values were stored as strings

**Symptom**

```text
TypeError: can't multiply sequence by non-int of type 'float'
```

After calculating demand multipliers, xl2times multiplies each base-year
`COM_PROJ` value by a float. The base-year values had been written as numeric
strings, so this multiplication failed.

**Resolution**

The following 427 cells were manually converted to numeric Excel cells:

| Workbook | Worksheet | Input column | Value cells |
| --- | --- | --- | --- |
| `VT_TIMESNZ_AGR.xlsx` | `AGR_Demand` | `Demand~2023` (`C217`) | `C218:C303` |
| `VT_TIMESNZ_COM.xlsx` | `COM_Demand` | `Demand~2023` (`C386`) | `C387:C475` |
| `VT_TIMESNZ_IND.xlsx` | `Industry demand` | `Demand` (`C639`) | `C640:C809` |
| `VT_TIMESNZ_RES.xlsx` | `Residential demand` | `Demand` (`C248`) | `C249:C304` |
| `VT_TIMESNZ_TRA.xlsx` | `TRA_Demand-Vehicles` | `2023` (`C363`) | `C364:C389` |

The upstream openpyxl generator should write these values as Python `int` or
`float` objects. Applying an Excel number format is not sufficient if the cell
value itself is still a string. A generated-workbook validation should confirm
that populated `~FI_T: Demand` value cells have numeric values and Excel data
type `n`.

The refreshed upstream-generated workbooks retain these cells as numeric Excel
values, so the manual correction is no longer required for the current
artifacts.

**Status:** Resolved in PREPARE-TIMES-NZ and retained in the refreshed
workbooks.

### Numeric input normalization initially converted `~StartYear` to a string

**Symptom**

```text
TypeError: unsupported operand type(s) for +: 'int' and 'str'
```

The failure occurred in `process_time_periods()` while xl2times added period
lengths to the model start year.

**Cause**

`~StartYear` is a singleton table: the cell immediately below the tag is its
value, not a header. The first upstream numeric-normalization pass treated that
cell as header-like and wrote `SysSettings.xlsx`, `SysSettings!A3` as the
string `"2023"`.

**Resolution**

The upstream generator now preserves this singleton value as an integer. The
refreshed workbook contains integer `2023`, and the current conversion passes
`process_time_periods()`.

This is an important validation case for the upstream writer: tag and header
cells should remain strings, but a singleton table value must be typed from its
content even though it appears directly below a tag.

**Status:** Resolved in PREPARE-TIMES-NZ and verified in the current run.

### Final fix-up attempts to round string-valued process lifetimes

**Symptom**

```text
TypeError: type str doesn't define __round__ method
```

The failure occurs in `apply_final_fixup()`. For processes with exactly one
non-zero `PRC_RESID` record, xl2times obtains the corresponding `LIFE` or
`NCAP_TLIFE` value and calls:

```python
round(value)
```

**Previous diagnosis**

`LIFE` was the source variable causing this error. xl2times normalizes it to
the TIMES attribute `NCAP_TLIFE`. The affected calculation contained 763
region/process records whose lifetime was still a string:

| Source workbook | Worksheet | Lifetime cells | Affected records |
| --- | --- | --- | ---: |
| `VT_TIMESNZ_IND.xlsx` | `Industry demand` | `J407:J635` | 206 |
| `VT_TIMESNZ_COM.xlsx` | `COM_Demand` | `J168:J382` | 199 |
| `SubRES_NewTechs_TRA_Steady.xlsx` | `TRA_NEW` | `H89:H175` | 114 |
| `VT_TIMESNZ_RES.xlsx` | `Residential demand` | `J121:J236` | 104 |
| `VT_TIMESNZ_AGR.xlsx` | `AGR_Demand` | `J109:J213` | 100 |
| `VT_TIMESNZ_TRA.xlsx` | `TRA_Demand-Vehicles` | `F200:F359` | 30 |
| `VT_TIMESNZ_ELC.xlsx` | `Existing Technologies` | `K107:K200` | 10 |

These were not seven isolated bad values. A scan of the earlier model inputs found
1,821 numeric-looking string cells under `LIFE` or `NCAP_TLIFE` headers across
30 tables. The 763 records above are the subset reached by this particular
stock-expiry calculation; multiple regions can refer to the same source cell.

**Resolution**

PREPARE-TIMES-NZ now emits the affected populated lifetime cells as numeric
Excel values. A targeted audit of all seven ranges above found only Python
`int` and `float` values and no strings. The current run completed
`apply_final_fixup()` successfully, confirming the correction end-to-end.

**Compatibility follow-up**

When a qualifying process has no `LIFE` or `NCAP_TLIFE` value, xl2times uses a
hard-coded default lifetime of 30 years when calculating the implied
`PRC_RESID = 0` year. Confirm the corresponding VEDA behaviour and default
before relying on missing lifetime values. If VEDA uses a different default or
derives the expiry year differently, xl2times could silently create different
stock trajectories even after the string-type error is resolved.

**Follow-up investigation**

Compare xl2times's 30-year missing-lifetime default with VEDA using a minimal
test process or VEDA-generated DD output.

**Status:** Resolved in PREPARE-TIMES-NZ and confirmed end-to-end.

### `~TFM_AVA` tables used `AllRegions` where xl2times expects `Value`

**Symptom**

```text
KeyError: ['value']
```

The failure occurs in `process_transform_availability()` when it unconditionally
calls `dropna(subset="value")`.

**Affected inputs**

- `SubRES_NewTech_Storage_Steady_trans.xlsx`, worksheet `AVA`, range `A3:C7`;
- `SubRES_NewTech_Storage_Shift_trans.xlsx`, worksheet `AVA`, range `A3:C7`.

The failing workbooks previously contained:

```text
PSet_PN       AllRegions
ELC_BAT_2H    1
ELC_BAT_8H    1
ELC_BAT_DIST  1
```

**Cause**

For a `~TFM_AVA` table, xl2times recognizes actual model-region columns such as
`NI` and `SI`. If none are present, it expects a `Value` column and applies that
value to all regions. It does not recognize `AllRegions` as a region column in
this code path. It therefore adds a separate all-regions marker, drops the
input `AllRegions` column as unknown, and leaves the table without `value`.

**Resolution**

PREPARE-TIMES-NZ now writes `Value` as the second-column header in both tables,
with numeric `1` values. xl2times expands these values over `NI` and `SI`.

**Status:** Resolved in PREPARE-TIMES-NZ and verified in the current run.

### Commercial boiler SubRES processes lost their output topology

**Symptom**

The generated `TOP` table was missing 102 commercial-boiler output links: 51
new-technology processes in each of `NI` and `SI`. The processes and their
technical parameters were present, but their links to commercial heat-demand
commodities were absent.

**Cause**

`SubRES_NewTechs_COM.xlsx`, worksheet `COM_NEW`, used generic, undeclared
commodity names in the `Comm-Out` column for boiler technologies. For example,
`C_HLTH-WH-Boiler-PLT` specified `C_HLTH-Boiler-WH`, whereas the declared
commodity is `C_HLTH-WH`.

VEDA's generated DD input derived the expected demand output from the `DMD`
process convention/name and emitted `C_HLTH-WH` in `PRC_ACTUNT` and `TOP`.
xl2times instead retained the literal `Comm-Out` value; because that commodity
does not exist, the output topology link was not retained. This behaviour is
specific to the affected boiler rows, rather than a general failure to read
SubRES `~FI_T` tables.

**Resolution**

PREPARE-TIMES-NZ now writes the declared heat-demand commodity directly in
`Comm-Out` (for example, `C_HLTH-WH` rather than
`C_HLTH-Boiler-WH`) for all affected commercial boiler technologies. The
regenerated comparison has no missing commercial-boiler `TOP` rows; the 102
links now match the VEDA ground truth.

**Status:** Resolved in PREPARE-TIMES-NZ and verified in the regenerated
comparison output.

## Resolved by xl2times patch

### DD numeric values were truncated to 10 significant digits

**Symptom**

The generated DD files rounded all non-integer float values to 10 significant
digits. For example, the South Island winter energy margin coefficient was
written as `0.2785968988`, whereas VEDA wrote `0.278596898776721`.

**Cause**

xl2times 0.3.0's `convert_to_string()` explicitly formats floats using
`{value:.10g}` before the DD writer receives them. This is a numerical
conversion difference, rather than a display-only difference: the rounded
strings are the values read by GAMS.

**Resolution**

The project-local wrapper replaces `convert_to_string()` with equivalent
handling that uses `{value:.15g}` for non-integer Python floats. A scan of the
VEDA Steady DD files found a maximum of 15 significant digits in numeric
values, so this aligns generated DD precision with the reference exporter
without modifying the installed xl2times package.

Implementation: `src/solve_times_nz/xl2times_compat.py`

**Status:** Resolved locally. Rebuild and re-solve before using result-level
comparisons to investigate remaining compatibility differences.

### Environmental `FLO_EMIS` output links were omitted from `TOP`

**Symptom**

The converted all-scenario `TOP` table omitted 18 environmental output links:
the 16 NI geothermal process → `ELCCO2` links and the two NI gas-production
process → `GASCO2` links.  Their corresponding `FLO_EMIS` values were present.

**Cause**

The TIMES definition of `FLO_EMIS` makes an ENV-targeted emission factor an
implicit output flow when that commodity is otherwise absent from a process's
topology.  xl2times correctly derives these rows as `model.implied_topology`
for user-constraint validation, but `complete_dictionary()` previously wrote
only `model.topology` to the exported `Topology` table.  Thus the implied rows
never reached `TOP` in the generated DD files.

**Resolution**

The project-local `xl2times-fixed` wrapper now appends the derived
environmental links to the exported `Topology` dictionary, deduplicated on
`region`, `process`, `commodity`, and `io`.  It does not alter physical process
topology during conversion.

This is the intended TIMES behaviour: for example,
`ENV_ACT~GASCO2~NI` on `MINNGA-KAP` becomes
`FLO_EMIS(NI, year, MINNGA-KAP, ACT, GASCO2, ANNUAL)` and therefore implies
`TOP(NI, MINNGA-KAP, GASCO2, OUT)`.  `Comm-OUT=NGA` remains the process's
physical output and must not be changed to include `GASCO2`.

Implementation: `src/xl2times_test/cli.py`

Verification: the regenerated comparison has no missing `TOP` rows.  It has
20 additional environmental links, exactly corresponding to the existing
additional geothermal `FLO_EMIS` source rows: 18 are SI links and two are
extra NI Ngawha links.

**Status:** Resolved locally.  The separate extra geothermal `FLO_EMIS`
source-row issue still needs cleaning in PREPARE-TIMES-NZ; this patch correctly
exports its corresponding implied topology too.

### Generic `UC_FLO` terms lost regions from `R_E` / `R_S` sets

**Symptom**

The national `UC_WEM` constraint declares `~UC_Sets: R_S: NI, SI`. VEDA
emits its generic `UC_FLO` term for both regions, but xl2times emitted only
the NI fall and winter terms. The two SI records for `G_ELC_LV` → `ELCDD`
were consequently absent.

**Cause**

`process_user_constraint_tables()` runs before xl2times has assembled the
complete model-region set. It filters the user constraint's declared regions
against the incomplete set and collapses a generic `UC_FLO` term to NI. By the
time normal region defaults are available, the distinction between the generic
term and an NI-only term has been lost.

**Resolution**

The project-local `xl2times-fixed` wrapper now detects a plain `UC_FLO`
column in a `~UC_T` table with exactly one `R_E` or `R_S` region set. It emits
that term once for every region declared by the set, while leaving explicitly
regional columns unchanged.

Implementation: `src/xl2times_test/cli.py`

Verification: the all-scenario comparison now has six `UC_FLO` rows matching
the six VEDA ground-truth rows exactly; the prior two missing SI WEM rows are
gone.

**Status:** Resolved locally.

### Optional process descriptions were treated as mandatory

**Symptom**

```text
KeyError: "['description'] not in index"
```

The failure occurred in `generate_topology_dictionary()` during wildcard
processing.

**Cause**

None of the merged `~FI_PROCESS` declarations supplied a description column.
Descriptions are optional in xl2times' input configuration, but the wildcard
code selected `model.processes[["process", "description"]]` unconditionally.

**Resolution**

The project-local `xl2times-fixed` wrapper adds empty `description` columns to
the process and commodity dataframes when absent, then invokes the installed
xl2times CLI. The installed package under `.venv` is not edited.

Implementation: `src/xl2times_test/cli.py`

Regression test: `tests/test_cli.py`

**Status:** Resolved locally. The conversion now completes `process_wildcards`.

### Consecutive zero demand-driver values caused division by zero

**Symptom**

```text
ZeroDivisionError: division by zero
```

The failure occurred in `_project_demands()` when a driver remained zero for
more than one year:

```python
series["driver"] / series["driver_t-1"]
```

**Cause**

VEDA accepts this input and emits zero `COM_PROJ` values for every year after
the driver reaches zero. xl2times 0.3.0 correctly computes the first
positive-to-zero transition, but then attempts `0 / 0` in the following year.
It has no special handling for a demand that remains at zero.

The affected model series are:

- `IND_METH_DMD`, zero from 2027 in both Shift and Steady;
- `IND_STEEL_EAF_DMD`, zero from 2036 in Shift.

**Resolution**

The project-local wrapper now treats `0 -> 0` as a neutral driver ratio of
`1`. The cumulative projection multiplier is already zero after the initial
positive-to-zero transition, so the resulting demand remains exactly zero.

The wrapper deliberately rejects `0 -> non-zero` with a diagnostic error. A
demand restart cannot be derived from a percentage change relative to zero and
must instead be represented using explicit demand projections.

Implementation: `src/xl2times_test/cli.py`

Regression tests: `tests/test_cli.py`

**Status:** Resolved locally and covered by focused regression tests.

### Derived `PRC_RESID` rows exceeded VEDA's 2200 year domain

**Symptom**

`ELC_HYDSC_GENERIC` has a 200-year lifetime from 2023. xl2times therefore
derived zero `PRC_RESID` rows for 2223, which required expanding the generated
GAMS run's `EOTIME` to 2250.

**Cause**

The established VEDA run uses the default 2200 end year. Its input domain does
not contain 2223, so it cannot retain that derived expiry row. Extending only
the xl2times run changed the terminal horizon and made result comparisons
non-equivalent.

**Resolution**

The project-local wrapper now removes only derived zero `PRC_RESID` rows after
2200. Explicit source data and process lifetimes are retained. The generated
run template again sets `EOTIME = 2200`, matching VEDA's effective domain.

**Status:** Resolved locally; rebuild and re-solve before comparing objectives.

## Non-fatal warnings to revisit

The following messages have not stopped conversion but may indicate incomplete
xl2times 0.3.0 configuration support:

- Several `Tag` enum values are absent from the bundled `veda-tags.json`,
  including `tfm_ava_c`, `tfm_fill_r`, `time_slices`, `tradelinks`, and
  `uc_sets`.
- `~IMPSETTINGS` is unrecognized and its table is dropped.
- Several tags have no entry in `config.column_aliases`, including
  `~TRADELINKS`, `~STARTYEAR`, `~ACTIVEPDEF`, `~TIMEPERIODS`, `~CURRENCIES`,
  `~DEFUNITS`, and `~TIMESLICES`.
- Region specifications in the `LNG` sheets of
  `SubRES_LNG_Imports_Steady.xlsx` and `SubRES_LNG_Imports_Shift.xlsx` are reset
  because xl2times does not support that dimension there.
- pandas emits a `DataFrameGroupBy.apply` future-deprecation warning in
  `include_cgs_in_topology`.
