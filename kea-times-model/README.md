Steps. The following is not yet working but documents my current attempt to replicate the use of VEDA to run TIMES using the open-source [`xl2times` tool](https://github.com/etsap-TIMES/xl2times). The hope is to create a CICD pipeline using GitHub actions that can generate, run, and publish the results from `TIMES-NZ` when triggered by a user.

## Generate TIMES model using VEDA
* Import the TIMES model contained in this directory using Veda2-LocalHost.
* Define a scenario called `veda-kea-output` that uses all files.
* Run the scenario.
* Retrieve the `veda-kea-output` GAMS files:
```Powershell
.\get_from_veda.ps1 C:\Users\CattonW\Veda2\Veda\GAMS_WrkTIMES\ veda-kea-output
```
* Run the `veda-kea-output` scenario:
```Powershell
.\run_times_scenario veda-kea-output
```
This attempts to enter the `veda-kea-output` directory and from there to run the command
```Powershell
GAMS veda-kea-output.RUN IDIR=C:\Users\CattonW\Veda2\Veda\GAMS_SrcTIMES.v4.7.6 GDX=C:\Users\cattonw\git\TIMES-NZ-Model-Files\kea-times-model\GAMSSAVE\veda-kea-output PS=99999 r=C:\Users\CattonW\Veda2\Veda\GAMS_SrcTIMES.v4.7.6\_times
```
This appears to work and provide the same objective function value as running the model in VEDA:
```Powershell
grep Objective .\veda-kea-output\veda-kea-output.lst
```

## Generate TIMES model using xl2times
* This step assumes that the `times_excel_reader` docker container has been built following the instructions in `..\README.md`
* Run the following command to generate GAMS files in the `xl2times-kea-output` directory:
```Powershell
docker run -it --rm --name my_times_reader -v ${PWD}:/usr/src/app/TIMES-NZ-KEA times_excel_reader xl2times TIMES-NZ-KEA/ --output_dir TIMES-NZ-KEA/xl2times-kea-output/ --regions NI,SI --dd
```
* Run the `xl2times-kea-output` scenario:
```Powershell
.\run_times_scenario.ps1 xl2times-kea-output
```
This attempts to enter the `xl2times-kea-output` directory and from there to run the command
```Powershell
GAMS xl2times-kea-output.RUN IDIR=C:\Users\CattonW\Veda2\Veda\GAMS_SrcTIMES.v4.7.6 GDX=C:\Users\cattonw\git\TIMES-NZ-Model-Files\kea-times-model\GAMSSAVE\xl2times-kea-output PS=99999 r=C:\Users\CattonW\Veda2\Veda\GAMS_SrcTIMES.v4.7.6\_times
```
Currently it doesn't work, and throws a large number of "Domain violation for element" errors.
