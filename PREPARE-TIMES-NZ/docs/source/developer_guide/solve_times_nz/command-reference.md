# Command and artefact reference

Run commands from `SOLVE-TIMES-NZ`. The examples below use the versioned
workspace command so that the installed tools and locked dependencies are used.

## Commands

### Resolve

```bash
uv run solve-times-nz resolve cases/steady.toml
```

`resolve` reads a case manifest and prints the final, precedence-ordered list
of selected workbooks. It does not create files. Use it after any change to a
case, workbook group, or file-order configuration.

| Argument or option | Meaning |
| --- | --- |
| `case` | Required path to the TOML case manifest. |
| `--input-root PATH` | Prepared-workbook root. Defaults to `PREPARE-TIMES-NZ/output` in the repository. |
| `--groups PATH` | Alternative `input-groups.toml`; useful for a controlled experiment. |
| `--file-order PATH` | Alternative `input-order.toml`; use only when its ordering has been reviewed with the corresponding groups file. |

Resolution fails when the input root does not exist, a group is unknown or
cyclic, a file pattern matches nothing, a selected file is not an Excel
workbook, or a selected workbook has no entry in the file-order list.

### Build

```bash
uv run solve-times-nz build cases/steady.toml
```

`build` has the same case-selection options as `resolve`, then runs the
project-owned xl2times wrapper and renders the TIMES run file. It replaces its
output directory; do not point `--output` at hand-maintained files.

| Argument or option | Meaning |
| --- | --- |
| `case` | Required path to the TOML case manifest. |
| `--input-root`, `--groups`, `--file-order` | Same meaning as for `resolve`. |
| `--output PATH` | Override the generated case directory. The default is `build/cases/<case>-v<workspace-version>`. |

The default output is deliberately version stamped. The `solve` command only
looks in that default location, so a custom output is for inspection or DD
export work; rebuild normally before solving it.

### Solve

```bash
uv run solve-times-nz solve steady
```

`solve` stages the default generated case on the named local executor, runs
native Windows GAMS and GDX2VEDA, then copies VEDA results back to the
repository. The positional argument is the **case name**, not a path and not
the versioned directory name. It is resolved as
`build/cases/<case>-v<workspace-version>`.

| Argument or option | Meaning |
| --- | --- |
| `case` | Required case name, such as `steady`. |
| `--local-config PATH` | Local executor TOML. Defaults to `config/solve.local.toml`. |
| `--run-id ID` | Unique suffix for the staged run directory. It may contain letters, numbers, `-`, and `_`. Defaults to a UTC timestamp. |
| `--diagnostic` | After a successful solve, run GAMS CONVERT to retain the named matrix, dictionary, and CPLEX LP representation. This can be large. |

The staging directory must already exist. A run never overwrites an existing
staged directory or existing returned-results directory. Failed staged runs are
also retained for inspection.

After a successful solve and VEDA export, `solve` automatically creates the
post-processed parquet outputs. See [Post-processing solver
results](postprocessing.md) for the outputs and recovery workflow.

### Postprocess

```bash
uv run solve-times-nz postprocess build/solves/<case>-v<version>-<run-id>
```

Re-runs parquet generation from the copied raw `.vd` file without solving the
model again. It overwrites only that run's `postprocessed/` parquet files.

| Argument or option | Meaning |
| --- | --- |
| `run_dir` | Required completed solver-run directory. |
| `--metadata-dir PATH` | Override the copied metadata for a controlled comparison. Without it, post-processing uses the run's `postprocessed/metadata` CSV snapshot. |

## Generated and returned artefacts

The normal build directory is:

```text
SOLVE-TIMES-NZ/build/cases/<case>-v<workspace-version>/
  ts.dd                 # TIMES time-slice declaration
  output.dd             # generated TIMES sets and parameters
  milestonyr.dd         # model milestone years
  <case>.run            # rendered project run program
  cplex.opt             # copied only for a CPLEX case
  manifest.json         # input hashes, settings, templates, and build command
  raw_tables.txt        # xl2times diagnostic output, when produced
  merged_tables.txt     # xl2times diagnostic output, when produced
```

The manifest is the handover record for a build. It records the case manifest,
ordered source-workbook paths and SHA-256 hashes, converter command and
version, Python version, selected executor, solver settings, and hashes of the
run and CPLEX-option templates. It does not record a repository Git revision;
record that separately when preserving a formal baseline.

The native Windows staging directory is a timestamped or explicitly named
child of the executor's `staging_root`. It contains a copy of the generated
case and an updated manifest with staging and execution status. It is retained
after both success and failure.

Successful result packages are copied to:

```text
SOLVE-TIMES-NZ/build/solves/<case>-v<workspace-version>-<run-id>/
  <case>.vd, .vde, .vds, .vdt   # files emitted by GDX2VEDA
  manifest.json                 # build, staging, execution, and result record
  diagnostics/                  # only with --diagnostic
    diagnostic-matrix.gdx
    diagnostic-dictionary.gdx
    diagnostic-model.lp
```

The exact VEDA suffixes depend on what GDX2VEDA emits. `solve` requires at
least one of `.vd`, `.vde`, `.vds`, or `.vdt`; otherwise it records an export
failure and leaves the staged directory in place.

## Recovery and troubleshooting

| Symptom | First checks |
| --- | --- |
| `Input root does not exist` | Run `PREPARE-TIMES-NZ` first, or pass the intended `--input-root`. |
| A workbook has no file-order entry | Add its repository-relative path once to `config/input-order.toml`, at the required precedence position, then rerun `resolve`. |
| `solve` cannot find a generated case | Rebuild without `--output`; `solve` only uses the default version-stamped directory. |
| Local configuration or executor is missing | Copy `config/solve.local.example.toml`, set all three paths, and ensure the manifest's executor name matches an `[executors.<name>]` section. |
| GAMS or GDX2VEDA cannot be found | Check `gams.exe` and `gdx2veda.exe` below `gams_system_dir`, plus `_times.g00` and `times2veda.vdd` below `times_source_dir`. |
| A solve or export fails | Read the error, then inspect the retained native staging directory and its `manifest.json`. Do not edit the generated DD files in place; fix inputs/configuration and rebuild. |
| Diagnostic command has a non-zero exit code | It can still be accepted if all three requested diagnostic files were written; inspect those files and the manifest's `diagnostic_exit_code`. |

For the local Windows/WSL boundary and required paths, see [TIMES and GAMS
setup](times-gams-setup.md). For case composition, see [Scenario
configuration](scenario-configuration.md).
