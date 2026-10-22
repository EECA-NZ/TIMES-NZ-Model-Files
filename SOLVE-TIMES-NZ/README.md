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
