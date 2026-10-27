# TIMES and GAMS setup

This page describes the local software and paths needed to turn a generated
TIMES-NZ DD case into a GAMS solve. These are machine-specific details: do not
commit them to a case manifest or the repository.

For the first integration test, use the same GAMS installation and
`GAMS_SrcTIMES` version as the successful VEDA reference case. This removes a
generator-version change as a possible explanation for any difference. A newer
TIMES installation can be introduced later as a separate toolchain and tested
deliberately.

## Required local components

The initial Windows executor needs:

- Native Windows GAMS, with a valid licence and the licensed CPLEX solver.
- The known-good TIMES generator source directory used by VEDA, for example
  `GAMS_SrcTIMES.v4.8.3`. Treat this directory as read-only.
- The matching `VT_GAMS`, `GDX2VEDA`, and `times2veda.vdd` tools supplied with
  that generator installation.
- A writable, native Windows staging directory for generated case folders and
  solver outputs. Prefer a short independent location such as
  `C:\TIMES-NZ\runs`, rather than a VEDA-managed working folder.

When running `SOLVE-TIMES-NZ` in WSL, the staging directory must also be
visible through a mount such as `/mnt/c/TIMES-NZ/runs`. Do not run native
Windows GAMS directly against a `\\wsl$` repository path; stage the completed
case onto the Windows filesystem first.

## Toolchains and executors

A case chooses a portable *toolchain*, not a machine path:

```toml
[solve]
toolchain = "veda-times-4.8.3"
```

An executor is the local binding that makes a toolchain runnable on a given
machine. The same case could later use a native WSL/Linux executor, provided
that executor supports the selected toolchain. This separation keeps case
definitions portable while still recording the intended generator protocol.

## Configure this machine

Copy the versioned example without adding the real configuration to Git:

```bash
cd SOLVE-TIMES-NZ
cp config/solve.local.example.toml config/solve.local.toml
```

Edit `config/solve.local.toml` to name the local executor and its paths:

```toml
[executors.windows_veda]
kind = "windows"
toolchains = ["veda-times-4.8.3"]

# Path visible to the WSL process performing the copy.
staging_root = "/mnt/c/TIMES-NZ/runs"

# Paths consumed by native Windows tools.
gams_system_dir = "C:\\GAMS\\<version>"
times_source_dir = "C:\\Users\\searlel\\Veda\\GAMS_SrcTIMES.v4.8.3"
launcher = "C:\\Users\\searlel\\Veda\\GAMS_SrcTIMES.v4.8.3\\VT_GAMS"
result_exporter = "C:\\Users\\searlel\\Veda\\GAMS_SrcTIMES.v4.8.3\\GDX2VEDA"
```

Create the Windows staging directory before trying to stage a case. It must be
writable both through the WSL mount and by the Windows GAMS process.

## Stage a generated case

Build the case first, then stage it for the configured executor:

```bash
uv run solve-times-nz build cases/steady.toml --output build/cases/steady
uv run solve-times-nz stage build/cases/steady --executor windows_veda
```

`stage` creates a timestamped child directory below `staging_root`, copies the
complete generated case, adds staging information to its manifest, and refuses
to overwrite an existing staged run.

At present, staging is the final automated step. Native `VT_GAMS` invocation,
GDX2VEDA export, and return of solver results will be added after the reference
launcher command has been confirmed against the staged Steady case.
