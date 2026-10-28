# SOLVE-TIMES-NZ

Builds reproducible TIMES-NZ DD case inputs from selected Excel workbooks.
Each case selects a named local executor with a GAMS installation and TIMES
source.

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
files. The initial executor should point at the VEDA reference installation.

By default, workbook paths are resolved relative to
`PREPARE-TIMES-NZ/output`. Override this with `--input-root` when necessary.

## Local executors and staging

Copy [solve.local.example.toml](config/solve.local.example.toml) to
`config/solve.local.toml` and set the paths available on this machine. The
real local file is ignored by Git. A case selects one of the executor names in
that file.

Every path in the local executor configuration is interpreted by the process
running this command. Therefore, when WSL stages a case for native Windows
GAMS, use mounted paths for the staging root, GAMS installation, and TIMES
source—for example `/mnt/c/TIMES-NZ/runs` and `/mnt/c/Users/...`.

```bash
uv run solve-times-nz solve steady
```

`solve` copies a complete generated case to a unique run directory and invokes
native Windows GAMS, then runs GDX2VEDA. It retains the Windows run directory,
records the execution status in its manifest, and copies VEDA result files to
`build/solves/<case>-<run-id>/`.

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
