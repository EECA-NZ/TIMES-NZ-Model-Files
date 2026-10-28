# Scenario configuration

`PREPARE-TIMES-NZ` produces the Excel workbooks that describe a TIMES-NZ
model. `SOLVE-TIMES-NZ` is the adjacent project that selects a deliberate,
versioned set of those workbooks and exports the combined TIMES DD inputs.
It makes a case reproducible: a result can be traced back to its case
definition and the exact prepared workbooks used to create it.

The canonical prepared-workbook root is `PREPARE-TIMES-NZ/output`. The solver
configuration is held separately in `SOLVE-TIMES-NZ`:

```text
SOLVE-TIMES-NZ/
  config/input-groups.toml  # reusable workbook selections
  config/input-order.toml   # project-wide workbook precedence
  cases/                    # case manifests
  build/                    # generated, unversioned DD cases
```

## Available methods

The current implementation has three Linux-side commands. Run them from
`SOLVE-TIMES-NZ`.

### Resolve a case

`resolve` is a dry run. It reads a case manifest, expands its groups and
patterns, validates the selection, and prints the final workbook paths. It
does not create or modify a case directory.

```bash
uv run solve-times-nz resolve cases/steady.toml
```

Use `resolve` whenever a group or case changes. Keep its output with review
notes when a workbook selection is materially changed.

### Build DD inputs

`build` resolves the case, runs the project-owned `xl2times-fixed`
compatibility wrapper, and writes a generated DD case directory.

```bash
uv run solve-times-nz build cases/steady.toml \
  --output build/cases/steady
```

`build` replaces the requested generated output directory. A successful build
contains `ts.dd`, `milestonyr.dd`, `output.dd`, a generated `<case-name>.run`,
and `manifest.json`; the manifest records the resolved inputs, their hashes,
and the selected executor. Do not target a
directory containing hand-maintained files.

Solver installations and execution are configured separately from scenario
composition. See [TIMES and GAMS setup](times-gams-setup.md) before solving a
generated case. A successful DD export is not itself a completed model solve:
the generated case must still be executed by GAMS.

## Workbook groups

`config/input-groups.toml` is the catalogue of reusable selections. A group
is a semantic modelling component, not necessarily one workbook. For example,
a technology component can require its main workbook and a companion
`_trans.xlsx` workbook.

```toml
[groups.demand_flex_steady]
files = ["SubRES_TMPL/SubRES_DemandFlex_Steady.xlsx"]

[groups.steady_bundle]
includes = ["base", "demand_flex_steady"]
```

Use small groups for components that can be exchanged independently in a
sensitivity, such as demand flexibility, storage, carbon prices, or a demand
trajectory. Use a composite group only where that bundle has a stable meaning.
Avoid a catch-all pattern that silently incorporates a new workbook when the
preparation pipeline changes.

### Paths and wildcard patterns

Paths in `files` are relative to `PREPARE-TIMES-NZ/output`. They may use glob
patterns:

```toml
[groups.newtech_steady]
files = ["SubRES_TMPL/SubRES_NewTechs_*_Steady*.xlsx"]
```

Every pattern must match at least one file or resolution fails. This is a
deliberate guard against typos and missing preparation outputs. Confirm that a
wildcard does not capture an unintended workbook after adding or renaming
prepared files.

### Group rules

- Give a group a modelling name, rather than a name based only on its filename.
- Keep scenario alternatives separate: do not put Steady and Shift variants in
  the same ordinary group.
- Keep all workbooks for one component together, including required companion
  workbooks.
- Use `includes` to make a named bundle from smaller groups. Inclusion cycles
  are invalid.
- A group with no files and no included groups is not useful: it contributes
  nothing to a case and makes later review misleading.

## Case manifests

A file in `cases/` defines one reproducible case. It gives the case a name,
selects groups, and records converter and TIMES options.

```toml
name = "steady"
groups = [
    "base",
    "newtech_steady",
    "scenario_common",
    "scenarios_steady",
]

[solve]
executor = "windows_times_v483"

[xl2times]
regions = ["NI", "SI"]
include_dummy_imports = false

[times]
solver = "cplex"
reslim = 50000
```

The canonical Steady and Shift cases list their component groups explicitly.
This makes the case composition reviewable and avoids hiding a baseline behind
a broad, mutable composite group. A case may instead select a single composite
group when that is clearer.

The `executor` is user-defined; see [TIMES and GAMS setup](times-gams-setup.md)
for its local configuration.

### Experiments and overrides

Cases may inherit another manifest and deliberately alter its groups:

```toml
name = "steady-no-flex"
extends = "steady.toml"
remove_groups = ["demand_flex_steady"]
```

For a genuinely one-off workbook, use `add_files`; it is appended after the
selected groups and supports the same patterns as `files`.

```toml
add_files = ["SuppXLS/Scen_TransmissionSensitivity.xlsx"]
```

`remove_files` takes exact paths relative to the prepared-workbook root. Use
it sparingly: a named group substitution communicates model intent more
clearly and remains correct if that component gains another workbook.

## Ordering and reproducibility

Workbook order can matter when more than one workbook supplies overlapping
TIMES records. `config/input-order.toml` owns that order independently of case
composition. It is a single explicit list of workbook paths relative to
`PREPARE-TIMES-NZ/output`; its current sequence follows the VEDA Steady v309
DD include order as closely as the workbook-level inputs allow.

After resolving groups, patterns, additions, removals, and duplicates,
`resolve` sorts every selected workbook according to that list. Consequently,
changing a case's group order does not change workbook precedence. This makes
an experiment that selects the same files use the same input order as its
baseline.

Every selected workbook must have exactly one entry in `input-order.toml`.
Resolution fails for an unlisted selected workbook or a duplicate order entry;
add a new prepared workbook to its intended precedence position before adding
it to a group or case. This is deliberate: appending unknown files would be
deterministic but could silently change the meaning of overlapping records.

The selection process before the final ordering remains:

1. Groups appear in the order listed by the case manifest.
2. A composite group's `includes` are expanded in their listed order.
3. Each group's `files` entries are expanded in their listed order.
4. Matches for an individual wildcard are sorted alphabetically.
5. A duplicated workbook is retained only at its first appearance.
6. `add_files` is appended after group-derived files; `remove_files` is then
   filtered out.

The physical order of group tables in `input-groups.toml` has no effect. When
a change might affect an overlapping record, review the `resolve` output and
then compare the generated DD records with a known case.

## Modeller checklist

Before accepting a new or changed case:

1. Run `PREPARE-TIMES-NZ` so the selected workbooks exist in `output`.
2. Add or update the smallest appropriate groups in `input-groups.toml`.
3. Define or update the case manifest; prefer named groups over direct files.
4. Add every newly selected workbook to `input-order.toml` at its intended
   precedence position, then run `resolve` and review the complete ordered
   workbook list.
5. Run `build` into a new, empty directory.
6. Inspect the generated DD files and compare relevant records with the
   intended baseline or sensitivity case before solving.

Do not edit generated DD files in place. Change the prepared inputs, group
definitions, or case manifest, then build a fresh case directory.
