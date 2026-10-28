# The TIMES run file

Each built case contains a generated GAMS run program named after the case, for
example `steady.run`. It is rendered from
`SOLVE-TIMES-NZ/templates/times.run.template`; do not treat a staged copy as a
hand-maintained input. Change the template and rebuild the case instead.

The run file is deliberately independent of local Windows paths. The executor
supplies the TIMES source directory through the GAMS `IDIR` option when it
invokes the program.

## GAMS options

The opening `OPTION` statements select the LP solver and set execution limits,
listing behaviour, and solver output options. The selected solver and resource
limit are rendered from the case's `[times]` settings.

## TIMES switches

The `$SET` statements select the standard TIMES switches for this project,
including the restart/scratch mode, VEDA-compatible output behaviour, and
whether the model should solve. These are GAMS compile-time controls and must
appear before the relevant TIMES source is included.

## Time universe and time slices

`ts.dd` is included before TIMES initialisation because it declares the
time-slice hierarchy and its ordering.

`BOTIME` and `EOTIME` define the broad `ALLYEAR` universe used by the TIMES
source. They are not the model's optimisation horizon. In particular,
`EOTIME = 2250` permits data and lifetime-related years through 2250; the
milestone periods in `milestonyr.dd` still determine the years over which the
model is solved. Both settings must precede `initsys.mod`, where the TIMES
source declares `ALLYEAR`.

## Initialise TIMES and load case data

The run file then includes, in order:

1. `initsys.mod` and `initmty.mod` from the configured TIMES source, to declare
   the TIMES sets and parameters.
2. `output.dd`, the DD data generated from the selected Excel workbooks.
3. `milestonyr.dd`, which defines the model's milestone years.

This order is significant: the TIMES declarations must exist before generated
DD data is loaded, while the timeslice definitions must exist before the TIMES
initialisation code runs.

## Generate and solve

Finally, the run file assigns the case name and includes `maindrv.mod mod`.
`maindrv.mod` preprocesses the data, builds the optimisation model, and invokes
the selected GAMS solver when `SOLVE_NOW` is enabled.

## Changing a run setting

For a setting that applies to every generated case, change the run template and
rebuild. A one-off staged edit may help diagnose a problem, but it is not
reproducible and will be lost whenever the case is rebuilt and staged again.
