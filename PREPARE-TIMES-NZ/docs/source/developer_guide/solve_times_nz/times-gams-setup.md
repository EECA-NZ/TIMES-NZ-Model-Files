# TIMES and GAMS setup

The TIMES model generator is written in GAMS. While the TIMES code itself is open-source, GAMS and proprietary solvers are not. You will need a working GAMS installation and license to perform model solves.

Currently, this is built for a Windows GAMS installation while this repo operates in WSL. This is an unusual configuration, so the pipeline is designed for more flexible configuration setups relevant to your machine and tooling. 

## Required local components

The pipeline needs:

- A GAMS installation, with a valid license and the licensed CPLEX solver.
- TIMES model generator source code. 
- A writable, native Windows staging directory for generated case folders and
  solver outputs. 

Note that your staging directory must exist; the pipeline will note create it automatically. The developer can create it wherever is most appropriate. 

## Configure the Windows PATH

Add the configured Windows GAMS system directory—for example `C:\GAMS\44`—to
the native Windows `PATH`. This is required even though `gams_system_dir` is
also recorded in `solve.local.toml`: the current `VT_GAMS.CMD` calls `GAMS` by
name, and the VEDA run command calls `GDX2VEDA` by name. Both executables are
in the GAMS system directory.

Open a new native Windows Command Prompt after changing `PATH`, then verify:

```text
where GAMS
where GDX2VEDA
```

Both commands should resolve under the same configured GAMS installation.

## Installing the TIMES model generator

TIMES source files can be downloaded in an appropriate directory with:

```
git clone https://github.com/etsap-TIMES/TIMES_model.git
```
In general, it is best to simply keep this up to date. However, currently, this version points deliberately at the Veda-installed TIMES v4.8.3 for testing against older Veda versions. However, later this will need to be updated.

## Executors

This pipeline relies on `executors`, which are simple configuration items listing the locations of GAMS, TIMES source code, and the working directory. Current cases all include the named local executor that should run it:

```toml
[solve]
executor = "windows_times_v483"
```

An executor is the local binding that supplies GAMS, TIMES source, and a
staging directory on one machine. It is possible to define multiple executors for different cases. Because these may rely on machine-specific filepaths, they are deliberately ignored by git. 

### Configure your executors

You must create `solve.local.toml` in the `config/` directory, and define your executors there. This will identify the relevant locations for the pipeline to find your machine's GAMS installation and TIMES source code.

To get started, you can copy the example config file, eg:

```bash
cd SOLVE-TIMES-NZ
cp config/solve.local.example.toml config/solve.local.toml
```

Any given executor must contain:

- `staging_root`: The directory where GAMS and TIMES will write results, logs, etc.
- `gams_system_dir`: Location of your GAMS installation.
- `times_source_dir`: Location of your TIMES installation.

Edit `config/solve.local.toml` to name the local executor `[executors.your_name_here]` and its paths:

```toml
[executors.windows_times_v483]
staging_root = "/mnt/c/Users/<username>/TIMES-NZ/runs"
gams_system_dir = "/mnt/c/GAMS/<version>"
times_source_dir = "/mnt/c/Users/<username>/Veda/GAMS_SrcTIMES.v4.8.3"
```


It is recommended to use a descriptive executor name, for example `windows_times_v483` as above. This ensures its
underlying versions are apparent during review, and enables clear and easy changes to versions or configurations. It is the developer's responsibility to ensure their named executor is configured to the appropriate GAMS and TIMES versions such that the chosen name actually means something. 

Please note you must create the defined staging directory yourself before trying to stage a case. It must be
writable both through the WSL mount and by the GAMS process.

## Stage a generated case

Build the case first, then stage it for the configured executor:

```bash
uv run solve-times-nz build cases/steady.toml --output build/cases/steady
uv run solve-times-nz stage build/cases/steady
```

`stage` creates a timestamped child directory below `staging_root`, copies the
complete generated case, adds staging information to its manifest, and refuses
to overwrite an existing staged run.

At present, staging is the final automated step. Native `VT_GAMS` invocation,
GDX2VEDA export, and return of solver results will be added after the reference
launcher command has been confirmed against the staged Steady case.
