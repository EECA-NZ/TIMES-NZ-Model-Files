# SOLVE-TIMES-NZ

Builds reproducible TIMES-NZ DD case inputs from selected Excel workbooks.
Each case selects a portable TIMES toolchain; machine-local executors bind that
toolchain to a Windows or native GAMS installation.

Populate `config/input-groups.toml`. You can inspect a case before building it with `resolve`:

```bash
uv run solve-times-nz resolve cases/steady.toml
```
Build a case with `build`:
```
uv run solve-times-nz build cases/steady.toml --output build/cases/steady
```

`build` replaces the requested generated output directory on each run. Do not
use it to target a directory containing hand-maintained files.
It also renders a path-independent `<case-name>.run` program alongside the DD
files. The initial supported toolchain is `veda-times-4.8.3`, matching the
VEDA reference case.

By default, workbook paths are resolved relative to
`PREPARE-TIMES-NZ/output`. Override this with `--input-root` when necessary.

## Local executors and staging

Copy [solve.local.example.toml](config/solve.local.example.toml) to
`config/solve.local.toml` and set the paths available on this machine. The
real local file is ignored by Git. An executor is not part of a case
definition: it describes one local way to run a named toolchain.

`staging_root` must be visible to the process running this command. Therefore,
when WSL stages a case for native Windows GAMS, use a mounted path such as
`/mnt/c/TIMES-NZ/runs`.

```bash
uv run solve-times-nz stage build/cases/steady --executor windows_veda
```

`stage` copies a complete generated case to a unique run directory and refuses
to overwrite an existing staged run. It deliberately does not yet invoke
`VT_GAMS` or `GDX2VEDA`: their reference command line must first be validated
against the generated Steady case.

## Next steps

1. Populate `config/input-groups.toml` with the authoritative workbook set for
   the steady baseline.
2. Preview the resulting selection without changing any files:

   ```bash
   uv run solve-times-nz resolve SOLVE-TIMES-NZ/cases/steady.toml
   ```

3. Generate a throwaway DD smoke-test case:

   ```bash
   uv run solve-times-nz build SOLVE-TIMES-NZ/cases/steady.toml \
     --output SOLVE-TIMES-NZ/build/cases/steady
   ```

   Confirm it creates `ts.dd`, `output.dd`, `milestonyr.dd`, and
   `manifest.json`, then investigate any meaningful xl2times warnings.
4. Compare important generated records with the known VEDA steady case:
   `TOP`, `FLO_EMIS`, `UC_FLO`, demand projections, and lifetime-related
   values.
5. Reintroduce the successful Windows reference case. Use it to establish the
   generic `.run` template and confirm the exact `VT_GAMS` and GDX2VEDA
   commands.
6. Implement Windows staging, solving, result return, and baseline acceptance
   checks.
