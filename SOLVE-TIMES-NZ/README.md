# SOLVE-TIMES-NZ

Builds reproducible TIMES-NZ DD case inputs from selected Excel workbooks.
It currently supports Linux-side resolution and DD export only; Windows GAMS
and CPLEX execution will be added separately.

Populate `config/input-groups.toml`. You can inspect a case before building it with `resolve`:

```bash
uv run solve-times-nz resolve cases/steady.toml
```
Build a case with `build`:
```
uv run solve-times-nz build cases/steady.toml --output build/cases/steady
```

By default, workbook paths are resolved relative to
`PREPARE-TIMES-NZ/output`. Override this with `--input-root` when necessary.

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
